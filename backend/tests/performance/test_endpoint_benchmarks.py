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

"""What the read endpoints cost on synthetic data, measured with pytest-benchmark.

A module-scoped fixture seeds the test database once with
scripts/seed_performance_data.py (the profile is PERFORMANCE_PROFILE, small
by default) inside a transaction that is rolled back afterwards. Each scenario
calls one endpoint against the heaviest target in that data. pytest-benchmark
times the requests, and each benchmark's extra_info records the response
size, the number of SQL statements and their time, and the peak Python memory
of one request, measured with tracemalloc in a separate request.

Compare runs with pytest-benchmark's own options, for example:

    PERFORMANCE_PROFILE=medium uv run pytest tests/performance --benchmark-autosave
    PERFORMANCE_PROFILE=medium uv run pytest tests/performance --benchmark-compare
"""

import os
import time
import tracemalloc
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pytest_benchmark.fixture import BenchmarkFixture
from sqlalchemy import Connection, Engine, event, text
from sqlalchemy.orm import Session

from scripts.seed_performance_data import PROFILES, seed_performance_data
from test_observer.common.enums import Permission
from test_observer.data_access.setup import get_db
from test_observer.main import app
from tests.conftest import override_permissions

PROFILE = os.environ.get("PERFORMANCE_PROFILE", "small")
ROUNDS = int(os.environ.get("PERFORMANCE_ROUNDS", "3"))


@pytest.fixture(scope="module")
def seeded(db_engine: Engine) -> Iterator[Connection]:
    """A connection whose open transaction holds the seeded data."""
    connection = db_engine.connect()
    transaction = connection.begin()
    seed_performance_data(connection, PROFILES[PROFILE])
    yield connection
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="module")
def client(seeded: Connection) -> Iterator[TestClient]:
    def session() -> Iterator[Session]:
        with Session(bind=seeded, join_transaction_mode="create_savepoint") as db:
            yield db

    app.dependency_overrides[get_db] = session
    with override_permissions(*Permission):
        yield TestClient(app)
    del app.dependency_overrides[get_db]


@pytest.fixture(scope="module")
def scenarios(seeded: Connection) -> dict[str, tuple[str, dict[str, Any]]]:
    """Each scenario's path and query, against the heaviest target in the data."""
    # The newest execution with the most results has the longest history of
    # previous results to look up.
    execution_id = seeded.scalar(
        text(
            """SELECT test_execution_id FROM test_result
               GROUP BY test_execution_id ORDER BY count(*) DESC, test_execution_id DESC LIMIT 1"""
        )
    )
    reviewer_id = seeded.scalar(
        text(
            """SELECT ar.user_id FROM artefact_reviewers_association ar
               JOIN artefact a ON a.id = ar.artefact_id AND NOT a.archived
               GROUP BY ar.user_id ORDER BY count(*) DESC, ar.user_id LIMIT 1"""
        )
    )
    family = seeded.scalar(
        text("SELECT family::text FROM artefact WHERE NOT archived GROUP BY family ORDER BY count(*) DESC LIMIT 1")
    )
    artefact_id = seeded.scalar(
        text(
            """SELECT ab.artefact_id FROM artefact_build ab
               JOIN test_execution te ON te.artefact_build_id = ab.id
               GROUP BY ab.artefact_id ORDER BY count(*) DESC, ab.artefact_id DESC LIMIT 1"""
        )
    )
    test_case = seeded.scalar(
        text(
            """SELECT tc.name FROM test_result tr JOIN test_case tc ON tc.id = tr.test_case_id
               WHERE tr.test_execution_id = :execution_id ORDER BY tr.id LIMIT 1"""
        ),
        {"execution_id": execution_id},
    )
    reviewer = {"reviewer_ids": reviewer_id, "artefact_is_archived": "false"}
    return {
        "execution-search-1000": ("/v1/test-executions", reviewer | {"limit": 1000}),
        "execution-search-50": ("/v1/test-executions", reviewer | {"limit": 50}),
        "execution-search-50-latest": ("/v1/test-executions", reviewer | {"limit": 50, "execution_is_latest": "true"}),
        "execution-search-count": ("/v1/test-executions", reviewer | {"limit": 0}),
        "artefacts-family": ("/v1/artefacts", {"family": family}),
        "artefacts-all": ("/v1/artefacts", {}),
        "artefact": (f"/v1/artefacts/{artefact_id}", {}),
        "artefact-builds": (f"/v1/artefacts/{artefact_id}/builds", {}),
        "environment-reviews": (f"/v1/artefacts/{artefact_id}/environment-reviews", {}),
        "execution-results": (f"/v1/test-executions/{execution_id}/test-results", {}),
        "result-search-failed-1000": ("/v1/test-results", {"test_result_statuses": "FAILED", "limit": 1000}),
        "result-search-case-100": ("/v1/test-results", {"test_cases": test_case, "limit": 100}),
    }


SCENARIOS = [
    "execution-search-1000",
    "execution-search-50",
    "execution-search-50-latest",
    "execution-search-count",
    "artefacts-family",
    "artefacts-all",
    "artefact",
    "artefact-builds",
    "environment-reviews",
    "execution-results",
    "result-search-failed-1000",
    "result-search-case-100",
]


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_endpoint(
    benchmark: BenchmarkFixture,
    client: TestClient,
    seeded: Connection,
    scenarios: dict[str, tuple[str, dict[str, Any]]],
    scenario: str,
):
    path, params = scenarios[scenario]
    statements = 0
    sql_seconds = 0.0
    started: list[float] = []

    def before(*_: object) -> None:
        started.append(time.perf_counter())

    def after(*_: object) -> None:
        nonlocal statements, sql_seconds
        statements += 1
        sql_seconds += time.perf_counter() - started.pop()

    event.listen(seeded, "before_cursor_execute", before)
    event.listen(seeded, "after_cursor_execute", after)
    try:
        response = client.get(path, params=params)
    finally:
        event.remove(seeded, "before_cursor_execute", before)
        event.remove(seeded, "after_cursor_execute", after)
    assert response.status_code == 200
    response_bytes = len(response.content)
    del response

    tracemalloc.start()
    client.get(path, params=params)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    benchmark.extra_info.update(
        profile=PROFILE,
        response_bytes=response_bytes,
        sql_statements=statements,
        sql_ms=round(sql_seconds * 1000, 1),
        peak_python_mb=round(peak / 1e6, 1),
    )
    benchmark.pedantic(client.get, args=(path,), kwargs={"params": params}, rounds=ROUNDS, iterations=1)
