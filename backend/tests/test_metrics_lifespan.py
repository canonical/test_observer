# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""
Tests guaranteeing that a slow metrics initialization never blocks the main
event loop.

The core requirement is operational: the container must keep answering
Kubernetes probes even while metrics are being (re)built
from the database, which can take a long time. Because metrics initialization
is CPU/DB bound and synchronous, it is offloaded to a worker thread and started
as a background task from the lifespan handler. These tests pin that behaviour
so it cannot regress.

The tests deliberately avoid a real database or a real metrics server: the
blocking initialization is replaced with a ``threading.Event``-based blocker
and the Prometheus HTTP server is stubbed out. The blocker hangs the worker
thread until it is explicitly released at scenario teardown, and teardown waits
for the thread to confirm it finished, so it never leaks into other tests
(unlike a fixed ``time.sleep``, which a cancelled task cannot interrupt). Every
scenario runs under an overall timeout so a regression into blocking fails CI
fast instead of hanging. This keeps the suite fast and focused on concurrency
behaviour rather than metrics correctness.
"""

import asyncio
import logging
import queue
import threading
import time
import traceback
from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from typing import TypeVar
from unittest.mock import patch

import httpx

from test_observer import main

logger = logging.getLogger(__name__)

# Upper bound below which an operation is considered "prompt" — i.e. it did not
# wait on the (indefinitely blocked) metrics initialization. Generous enough to
# avoid CI flakiness while still far shorter than any real init would take.
THRESHOLD_SECONDS = 1.0

# Hard cap on any scenario. If the lifespan regresses into blocking (exactly
# what these tests guard against) the coroutine would otherwise hang forever;
# this makes CI fail fast with a clear timeout instead of stalling.
SCENARIO_TIMEOUT_SECONDS = 10.0

# How long the worker-thread blocker waits to be released before giving up on
# its own. Derived from the scenario timeout so it always outlives a healthy
# scenario (which releases it explicitly) but can never outlive the process.
WORKER_RELEASE_TIMEOUT_SECONDS = SCENARIO_TIMEOUT_SECONDS * 3

# How long teardown waits for the worker thread to confirm it finished, and how
# long a scenario waits for the blocker to signal it has started. Comfortably
# shorter than the scenario timeout so failures surface as clear assertions.
WORKER_FINISH_TIMEOUT_SECONDS = SCENARIO_TIMEOUT_SECONDS / 2

# How often the async pollers check a threading.Event. Kept in the tens-of-ms
# range so the tests stay responsive against the (1s) threshold while avoiding
# tight spinning that would waste CPU on shared/concurrent CI runners.
EVENT_POLL_INTERVAL_SECONDS = 0.02

T = TypeVar("T")


async def wait_for_event(event: threading.Event, timeout: float) -> bool:
    """
    Wait for a ``threading.Event`` from async code without consuming a thread.

    Deliberately avoids ``asyncio.to_thread`` / ``run_in_executor``: those would
    borrow a worker from the loop's default thread pool, coupling the test to
    executor capacity. If that pool were ever constrained the blocked metrics
    worker could occupy the only slot and this wait would never run. Polling
    ``is_set()`` under ``asyncio.sleep`` keeps the wait on the event loop.

    Returns ``True`` if the event fired within ``timeout``, ``False`` otherwise.

    A set event is always reported as success: it means the worker genuinely
    started, and whether it fired a poll-interval before or after the arbitrary
    deadline is not meaningful here (the real fail-fast guard is the overall
    ``SCENARIO_TIMEOUT_SECONDS`` wrapper). Reporting a timeout for an
    already-set event would only introduce flakiness from scheduler delays.
    """
    deadline = time.monotonic() + timeout
    while not event.is_set():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            # Re-check under the deadline: the event may have been set between
            # the loop condition and here, in which case that is still success.
            return event.is_set()
        # Never sleep past the deadline so the loop stays responsive.
        await asyncio.sleep(min(EVENT_POLL_INTERVAL_SECONDS, remaining))
    return True


def run_scenario(scenario_factory: Callable[[], Awaitable[T]]) -> T:
    """
    Run a scenario coroutine under an overall timeout so CI fails fast.

    Accepts a *factory* rather than an awaitable object so the awaitable is
    always constructed on the thread/loop that consumes it.

    These are synchronous tests, so we simply drive a fresh event loop via
    ``asyncio.run``. If this is ever called from within an already-running loop
    (e.g. an async test runner), ``asyncio.run`` raises a clear ``RuntimeError``
    rather than silently misbehaving; adopt an async runner at that point.
    """

    async def _runner() -> T:
        return await asyncio.wait_for(scenario_factory(), timeout=SCENARIO_TIMEOUT_SECONDS)

    return asyncio.run(_runner())


@contextmanager
def blocking_metrics_init() -> Iterator[threading.Event]:
    """
    Patch metrics initialization with a worker-thread blocker that hangs until
    explicitly released, yielding an Event that fires once the blocker has
    actually started running on the worker thread.

    The blocker waits on a ``threading.Event`` rather than sleeping for a fixed
    duration. It is always released on exit (even if the test body raises), and
    teardown waits for the worker thread to confirm it has finished, so the
    thread never lingers in the executor pool or leaks into other tests. Safety
    timeouts guard against the thread living forever if a signal is missed.
    """
    started_event = threading.Event()
    release_event = threading.Event()
    finished_event = threading.Event()
    # Captures a formatted traceback for any exception raised on the worker
    # thread. Assertions there run off the main thread and would otherwise be
    # swallowed by the background task (which catches Exception), producing
    # false-green runs. We stash the *formatted* traceback (not the exception
    # object) so teardown can raise a fresh, clearly-worded error on the main
    # thread rather than replaying frames that originated on another thread. A
    # SimpleQueue gives thread-safe handoff without reasoning about memory
    # visibility. We deliberately do not capture BaseException
    # (KeyboardInterrupt/SystemExit) so aborting the test run stays clean.
    worker_tracebacks: queue.SimpleQueue[str] = queue.SimpleQueue()

    # Accept arbitrary args so the blocker stays compatible with whatever
    # signature ``_initialize_all_metrics`` has (autospec validates the call
    # against the real signature, then forwards those args to this side_effect).
    def blocking_init(*_args: object, **_kwargs: object) -> None:
        started_event.set()
        try:
            # Record loudly if we are never released: a timeout here means the
            # blocking behaviour under test did not actually hold, and letting
            # the initializer "succeed" would hide that.
            if not release_event.wait(timeout=WORKER_RELEASE_TIMEOUT_SECONDS):
                raise AssertionError("Metrics blocker was never released; blocking behaviour did not hold")
        except Exception:  # noqa: BLE001 - surfaced on the main thread in teardown
            worker_tracebacks.put(traceback.format_exc())
            raise
        finally:
            finished_event.set()

    # autospec makes these patches fail loudly if the production signatures
    # change, instead of silently passing against an incompatible API.
    with (
        patch.object(main, "start_http_server", autospec=True),
        patch.object(main, "_initialize_all_metrics", autospec=True) as mock_init,
    ):
        mock_init.side_effect = blocking_init
        body_exc: BaseException | None = None
        try:
            yield started_event
        except BaseException as exc:
            body_exc = exc
            raise
        finally:
            try:
                release_event.set()
                # The worker thread may only be picked up from the pool after
                # teardown begins. Wait a generously bounded period for it to
                # start *before* the patches are removed, so a late-starting
                # thread can't call the real initializer and leak work into
                # later tests. Fail if it never starts (the patches would
                # otherwise be removed while a late worker could still invoke
                # the real initializer), and always wait for it to finish once
                # started.
                assert started_event.wait(timeout=WORKER_FINISH_TIMEOUT_SECONDS), (
                    "Metrics worker thread never started; cannot guarantee it will "
                    "not run the real initializer after patches are removed"
                )
                assert finished_event.wait(timeout=WORKER_FINISH_TIMEOUT_SECONDS), (
                    "Metrics worker thread did not finish after release; "
                    "a lingering thread could cause cross-test interference"
                )
                # Surface any exception raised on the worker thread so a missed
                # or timed-out release fails the test instead of passing green.
                # We raise a fresh error on the main thread and embed the
                # worker's formatted traceback in the message, since replaying
                # frames from another thread produces misleading stack traces.
                try:
                    worker_traceback = worker_tracebacks.get_nowait()
                except queue.Empty:
                    pass
                else:
                    raise AssertionError(f"Metrics worker thread raised:\n{worker_traceback}")
            except Exception:
                # A teardown failure must not mask a genuine failure from the
                # scenario body (e.g. an asyncio.wait_for timeout), which is the
                # more actionable signal. If the body already raised, log the
                # teardown problem and let the original propagate; otherwise the
                # teardown failure is itself the result and should surface.
                if body_exc is None:
                    raise
                logger.exception("Error during blocking_metrics_init teardown (masked by scenario failure)")


def test_lifespan_startup_does_not_wait_for_slow_metrics_init():
    """
    Application startup (the lifespan enter) must complete promptly and not
    await the potentially long-running metrics initialization.
    """

    async def scenario() -> float:
        start = time.monotonic()
        async with main.app.router.lifespan_context(main.app):
            startup_duration = time.monotonic() - start
            # Wait for the worker to actually start while the lifespan context
            # is still open. This is not just a sanity check: the lifespan exit
            # cancels the background task, so if we left the context before the
            # thread pool picked up the work the task could be cancelled before
            # it ever ran. Assert here so a regression that never schedules the
            # worker fails directly, rather than only later via teardown.
            started = await wait_for_event(started_event, WORKER_FINISH_TIMEOUT_SECONDS)
            assert started, "Startup did not schedule metrics initialization"
            return startup_duration

    with blocking_metrics_init() as started_event:
        startup_duration = run_scenario(scenario)

    assert startup_duration < THRESHOLD_SECONDS


def test_health_endpoint_responds_during_slow_metrics_init():
    """
    End-to-end check of the operational goal: the liveness probe responds
    quickly while metrics initialization is still running in the background.
    """

    async def scenario() -> tuple[int, dict[str, str], float]:
        transport = httpx.ASGITransport(app=main.app, client=("127.0.0.1", 12345))
        async with (
            main.app.router.lifespan_context(main.app),
            httpx.AsyncClient(transport=transport, base_url="http://testserver") as client,
        ):
            # Deterministically ensure metrics init is actually running (and
            # blocking) before probing, so the test genuinely exercises the
            # concurrent overlap rather than racing the background task.
            started = await wait_for_event(started_event, WORKER_FINISH_TIMEOUT_SECONDS)
            assert started, "Metrics initialization did not start; cannot test concurrent overlap"
            start = time.monotonic()
            # We use Test Observer's liveness probe as a proxy for Kubernetes liveness/readiness probes
            response = await client.get("/health/live")
            elapsed = time.monotonic() - start
            return response.status_code, response.json(), elapsed

    with blocking_metrics_init() as started_event:
        status_code, body, elapsed = run_scenario(scenario)

    assert status_code == 200
    assert body.get("status") == "live"
    assert elapsed < THRESHOLD_SECONDS
