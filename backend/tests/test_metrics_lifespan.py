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
import threading
import time
from collections.abc import Coroutine, Iterator
from contextlib import contextmanager
from typing import TypeVar
from unittest.mock import patch

import httpx

from test_observer import main

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

T = TypeVar("T")


def run_scenario(coroutine: Coroutine[object, object, T]) -> T:
    """Run a scenario coroutine under an overall timeout so CI fails fast."""

    async def _runner() -> T:
        return await asyncio.wait_for(coroutine, timeout=SCENARIO_TIMEOUT_SECONDS)

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

    def blocking_init() -> None:
        started_event.set()
        try:
            release_event.wait(timeout=WORKER_RELEASE_TIMEOUT_SECONDS)
        finally:
            finished_event.set()

    with (
        patch.object(main, "start_http_server"),
        patch.object(main, "_initialize_all_metrics", blocking_init),
    ):
        try:
            yield started_event
        finally:
            release_event.set()
            # Ensure the worker thread observed the release and exited before
            # the next test runs, so no background work leaks across tests.
            if started_event.is_set():
                assert finished_event.wait(timeout=WORKER_FINISH_TIMEOUT_SECONDS), (
                    "Metrics worker thread did not finish after release; "
                    "a lingering thread could cause cross-test interference"
                )


def test_lifespan_startup_does_not_wait_for_slow_metrics_init():
    """
    Application startup (the lifespan enter) must complete promptly and not
    await the potentially long-running metrics initialization.
    """

    async def scenario() -> float:
        start = time.monotonic()
        async with main.app.router.lifespan_context(main.app):
            # Startup has finished here; measure how long it took.
            return time.monotonic() - start

    with blocking_metrics_init():
        startup_duration = run_scenario(scenario())

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
            start = time.monotonic()
            # This is Test Observer's own liveness probe, which is not necessarily what Kubernetes probes.
            # But, we will use it as a proxy for the same behavior
            response = await client.get("/health/live")
            elapsed = time.monotonic() - start
            return response.status_code, response.json(), elapsed

    with blocking_metrics_init():
        status_code, body, elapsed = run_scenario(scenario())

    assert status_code == 200
    assert body == {"status": "live"}
    assert elapsed < THRESHOLD_SECONDS


def test_slow_metrics_init_is_cancelled_on_shutdown():
    """
    Shutdown must not hang waiting for an in-flight metrics initialization; the
    background task is cancelled and shutdown completes promptly.
    """

    async def scenario(started_event: threading.Event) -> float:
        async with main.app.router.lifespan_context(main.app):
            # Wait for a definitive signal that the background metrics task has
            # actually started running, rather than relying on a fixed sleep.
            started = await asyncio.to_thread(started_event.wait, WORKER_FINISH_TIMEOUT_SECONDS)
            assert started, (
                "Background metrics initialization never started; cannot validate cancellation-on-shutdown behaviour"
            )
            shutdown_start = time.monotonic()
        # Exiting the context above ran shutdown.
        return time.monotonic() - shutdown_start

    with blocking_metrics_init() as started_event:
        shutdown_duration = run_scenario(scenario(started_event))

    assert shutdown_duration < THRESHOLD_SECONDS
