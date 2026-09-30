#!/usr/bin/env python

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

"""Measure what the read endpoints cost on the data in the database.

Runs the application in process and calls each endpoint through FastAPI's
test client, so it measures the server side only: routing, queries, ORM
loading and serialisation, without network or client parsing. For each
scenario it reports:

- wall time, the median and the maximum over --runs requests,
- response size,
- SQL statements executed and the time the database spent on them,
- the peak Python memory allocated while serving one request, measured in a
  separate request with tracemalloc because tracing slows everything down.

Targets are picked from the data: the reviewer with the most assigned
artefacts, the artefact with the most executions, the execution with the most
previous results, and so on. Seed the database first, for example with
scripts/seed_performance_data.py.

Usage:
    python scripts/benchmark_endpoints.py [--runs N] [--scenario NAME ...]
        [--json PATH]
"""

import argparse
import json
import statistics
import sys
import time
import tracemalloc
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Connection, Engine, event, text

from test_observer.common.enums import Permission
from test_observer.controllers.applications.application_injection import get_current_application
from test_observer.data_access.models import Application


@dataclass(frozen=True)
class Scenario:
    name: str
    path: str
    params: dict[str, Any]


@dataclass
class Measurement:
    scenario: str
    status: int
    items: int | None
    response_bytes: int
    median_ms: float
    max_ms: float
    sql_statements: int
    sql_ms: float
    peak_python_mb: float


class SqlCounter:
    """Counts the statements an engine executes and the time they take."""

    def __init__(self, engine: Engine):
        self.engine = engine
        self.statements = 0
        self.seconds = 0.0
        self._started: list[float] = []

    def _before(self, *_: object) -> None:
        self._started.append(time.perf_counter())

    def _after(self, *_: object) -> None:
        self.statements += 1
        self.seconds += time.perf_counter() - self._started.pop()

    @contextmanager
    def listening(self) -> Iterator["SqlCounter"]:
        self.statements = 0
        self.seconds = 0.0
        event.listen(self.engine, "before_cursor_execute", self._before)
        event.listen(self.engine, "after_cursor_execute", self._after)
        try:
            yield self
        finally:
            event.remove(self.engine, "before_cursor_execute", self._before)
            event.remove(self.engine, "after_cursor_execute", self._after)


def pick_targets(connection: Connection) -> dict[str, object]:
    """Choose the heaviest realistic target for each kind of request."""
    # The newest execution with the most results has the longest history of
    # previous results to look up.
    execution_id = connection.scalar(
        text(
            """SELECT test_execution_id FROM test_result
               GROUP BY test_execution_id ORDER BY count(*) DESC, test_execution_id DESC LIMIT 1"""
        )
    )
    return {
        "reviewer_id": connection.scalar(
            text(
                """SELECT ar.user_id FROM artefact_reviewers_association ar
                   JOIN artefact a ON a.id = ar.artefact_id AND NOT a.archived
                   GROUP BY ar.user_id ORDER BY count(*) DESC, ar.user_id LIMIT 1"""
            )
        ),
        "family": connection.scalar(
            text("SELECT family::text FROM artefact WHERE NOT archived GROUP BY family ORDER BY count(*) DESC LIMIT 1")
        ),
        "artefact_id": connection.scalar(
            text(
                """SELECT ab.artefact_id FROM artefact_build ab
                   JOIN test_execution te ON te.artefact_build_id = ab.id
                   GROUP BY ab.artefact_id ORDER BY count(*) DESC, ab.artefact_id DESC LIMIT 1"""
            )
        ),
        "execution_id": execution_id,
        "test_case": connection.scalar(
            text(
                """SELECT tc.name FROM test_result tr JOIN test_case tc ON tc.id = tr.test_case_id
                   WHERE tr.test_execution_id = :execution_id ORDER BY tr.id LIMIT 1"""
            ),
            {"execution_id": execution_id},
        ),
    }


def build_scenarios(targets: dict[str, object]) -> list[Scenario]:
    reviewer = {"reviewer_ids": targets["reviewer_id"], "artefact_is_archived": "false"}
    return [
        Scenario(
            "execution-search-1000",
            "/v1/test-executions",
            reviewer | {"limit": 1000},
        ),
        Scenario(
            "execution-search-50",
            "/v1/test-executions",
            reviewer | {"limit": 50},
        ),
        Scenario(
            "execution-search-50-latest",
            "/v1/test-executions",
            reviewer | {"limit": 50, "execution_is_latest": "true"},
        ),
        Scenario(
            "execution-search-count",
            "/v1/test-executions",
            reviewer | {"limit": 0},
        ),
        Scenario("artefacts-family", "/v1/artefacts", {"family": targets["family"]}),
        Scenario("artefacts-all", "/v1/artefacts", {}),
        Scenario("artefact", f"/v1/artefacts/{targets['artefact_id']}", {}),
        Scenario(
            "artefact-builds",
            f"/v1/artefacts/{targets['artefact_id']}/builds",
            {},
        ),
        Scenario(
            "environment-reviews",
            f"/v1/artefacts/{targets['artefact_id']}/environment-reviews",
            {},
        ),
        Scenario(
            "execution-results",
            f"/v1/test-executions/{targets['execution_id']}/test-results",
            {},
        ),
        Scenario(
            "result-search-failed-1000",
            "/v1/test-results",
            {"test_result_statuses": "FAILED", "limit": 1000},
        ),
        Scenario(
            "result-search-case-100",
            "/v1/test-results",
            {"test_cases": targets["test_case"], "limit": 100},
        ),
    ]


def _count_items(payload: object) -> int | None:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        for key in ("test_executions", "test_results"):
            value = payload.get(key)
            if isinstance(value, list):
                return len(value)
    return None


def measure(client: TestClient, counter: SqlCounter, scenario: Scenario, runs: int) -> Measurement:
    timings: list[float] = []
    for _ in range(runs):
        with counter.listening():
            started = time.perf_counter()
            response = client.get(scenario.path, params=scenario.params)
            timings.append(time.perf_counter() - started)
    status = response.status_code
    items = _count_items(response.json()) if status == 200 else None
    response_bytes = len(response.content)
    # Let the last response go before the traced request, so the peak is
    # that request's own.
    del response

    tracemalloc.start()
    tracemalloc.reset_peak()
    client.get(scenario.path, params=scenario.params)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return Measurement(
        scenario=scenario.name,
        status=status,
        items=items,
        response_bytes=response_bytes,
        median_ms=round(statistics.median(timings) * 1000, 1),
        max_ms=round(max(timings) * 1000, 1),
        sql_statements=counter.statements,
        sql_ms=round(counter.seconds * 1000, 1),
        peak_python_mb=round(peak / 1e6, 1),
    )


def format_table(measurements: Sequence[Measurement]) -> str:
    header = "| Scenario | Items | Response | Median | Max | SQL statements | SQL time | Peak Python memory |"
    rule = "|---|---:|---:|---:|---:|---:|---:|---:|"
    rows = [
        f"| {m.scenario} | {'' if m.items is None else m.items} | {m.response_bytes / 1e6:.2f} MB "
        f"| {m.median_ms:.0f} ms | {m.max_ms:.0f} ms | {m.sql_statements} | {m.sql_ms:.0f} ms "
        f"| {m.peak_python_mb:.1f} MB |"
        for m in measurements
    ]
    return "\n".join([header, rule, *rows])


@contextmanager
def authorised(app: FastAPI) -> Iterator[None]:
    """Serve every request as an application holding every permission."""
    app.dependency_overrides[get_current_application] = lambda: Application(
        name="benchmark", permissions=list(Permission)
    )
    try:
        yield
    finally:
        del app.dependency_overrides[get_current_application]


def run_benchmark(
    client: TestClient,
    connection: Connection,
    runs: int,
    selected: Sequence[str] = (),
) -> tuple[dict[str, object], list[Measurement]]:
    """Measure every selected scenario against the data `connection` sees.

    The application's sessions must use the engine behind `connection`, so
    their statements can be counted.
    """
    targets = pick_targets(connection)
    scenarios = [s for s in build_scenarios(targets) if not selected or s.name in selected]
    unknown = set(selected) - {s.name for s in scenarios}
    if unknown:
        raise ValueError(f"unknown scenarios: {', '.join(sorted(unknown))}")
    counter = SqlCounter(connection.engine)
    return targets, [measure(client, counter, scenario, runs) for scenario in scenarios]


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=int, default=3, help="timed requests per scenario")
    parser.add_argument("--scenario", action="append", default=[], help="run only this scenario, repeatable")
    parser.add_argument("--json", help="also write the measurements to this file")
    args = parser.parse_args(argv)

    from test_observer.data_access.setup import engine
    from test_observer.main import app

    with authorised(app), TestClient(app) as client, engine.connect() as connection:
        targets, measurements = run_benchmark(client, connection, args.runs, args.scenario)
    sys.stdout.write(f"Targets: {targets}\n\n{format_table(measurements)}\n")
    if args.json:
        with open(args.json, "w") as output:
            json.dump(
                {"targets": targets, "measurements": [asdict(m) for m in measurements]}, output, indent=2, default=str
            )


if __name__ == "__main__":
    main()
