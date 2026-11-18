# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from test_observer.common.config import MAX_RESULT_PAGE_LIMIT
from test_observer.common.enums import Permission
from test_observer.data_access.models import TestResult
from tests.conftest import override_permissions
from tests.data_generator import DataGenerator

SEARCH_PAGE_ENDPOINT = "/v1/test-results/search-page"


def _create_test_result(generator: DataGenerator) -> TestResult:
    unique = uuid4().hex
    environment = generator.gen_environment(name=f"search-page-env-{unique}")
    test_case = generator.gen_test_case(name=f"search-page-case-{unique}", category="search-page-category")
    artefact = generator.gen_artefact(name=f"search-page-artefact-{unique}", version="1.2.3", track="stable")
    artefact_build = generator.gen_artefact_build(artefact, architecture="arm64")
    test_execution = generator.gen_test_execution(artefact_build, environment, test_plan="search-page-plan")
    return generator.gen_test_result(test_case, test_execution)


def test_search_page_requires_view_test_permission(
    test_client: TestClient,
):
    anonymous_response = test_client.get(SEARCH_PAGE_ENDPOINT)
    assert anonymous_response.status_code == 403

    with override_permissions():
        insufficient_response = test_client.get(SEARCH_PAGE_ENDPOINT)
    assert insufficient_response.status_code == 403

    with override_permissions(Permission.view_test):
        permitted_response = test_client.get(SEARCH_PAGE_ENDPOINT)
    assert permitted_response.status_code == 200


def test_search_page_defaults_to_first_fifty_rows(
    test_client: TestClient,
    generator: DataGenerator,
):
    result = _create_test_result(generator)

    with override_permissions(Permission.view_test):
        response = test_client.get(SEARCH_PAGE_ENDPOINT)

    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert [row["test_result"]["id"] for row in body["test_results"]] == [result.id]


@pytest.mark.parametrize("limit", [1, MAX_RESULT_PAGE_LIMIT])
def test_search_page_accepts_limit_boundaries(
    test_client: TestClient,
    generator: DataGenerator,
    limit: int,
):
    _create_test_result(generator)

    with override_permissions(Permission.view_test):
        response = test_client.get(SEARCH_PAGE_ENDPOINT, params={"limit": limit})

    assert response.status_code == 200
    assert response.json()["limit"] == limit


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": MAX_RESULT_PAGE_LIMIT + 1},
        {"offset": -1},
    ],
)
def test_search_page_rejects_invalid_pagination(
    test_client: TestClient,
    params: dict[str, int],
):
    with override_permissions(Permission.view_test):
        response = test_client.get(SEARCH_PAGE_ENDPOINT, params=params)

    assert response.status_code == 422


def test_search_page_orders_equal_timestamps_by_descending_id(
    test_client: TestClient,
    db_session: Session,
    generator: DataGenerator,
):
    results = [_create_test_result(generator) for _ in range(3)]
    same_timestamp = datetime(2026, 1, 1, 12, 0, 0)
    for result in results:
        result.created_at = same_timestamp
    db_session.flush()

    with override_permissions(Permission.view_test):
        response = test_client.get(SEARCH_PAGE_ENDPOINT)

    assert response.status_code == 200
    returned_ids = [row["test_result"]["id"] for row in response.json()["test_results"]]
    assert returned_ids == sorted((result.id for result in results), reverse=True)


def test_search_page_applies_bounded_offset_and_limit(
    test_client: TestClient,
    db_session: Session,
    generator: DataGenerator,
):
    results = [_create_test_result(generator) for _ in range(5)]
    for index, result in enumerate(results):
        result.created_at = datetime(2026, 1, 1, 12, index, 0)
    db_session.flush()

    with override_permissions(Permission.view_test):
        response = test_client.get(SEARCH_PAGE_ENDPOINT, params={"limit": 2, "offset": 1})

    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == 2
    assert body["offset"] == 1
    expected_ids = sorted((result.id for result in results), reverse=True)[1:3]
    assert [row["test_result"]["id"] for row in body["test_results"]] == expected_ids
    assert len(body["test_results"]) <= 2
    assert "count" not in body


def test_search_page_response_is_compact_and_does_not_select_detail_fields(
    test_client: TestClient,
    db_session: Session,
    generator: DataGenerator,
):
    result = _create_test_result(generator)
    result.comment = "private result comment"
    result.io_log = "private result log"
    db_session.flush()

    statements: list[str] = []

    def capture_select(
        _connection: Connection,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: bool,
    ) -> None:
        if statement.lstrip().lower().startswith("select"):
            statements.append(statement.lower())

    connection = db_session.connection()
    event.listen(connection, "before_cursor_execute", capture_select)
    try:
        with override_permissions(Permission.view_test):
            response = test_client.get(SEARCH_PAGE_ENDPOINT)
    finally:
        event.remove(connection, "before_cursor_execute", capture_select)

    assert response.status_code == 200
    body = response.json()
    assert "count" not in body
    assert len(body["test_results"]) == 1
    row = body["test_results"][0]
    assert set(row) == {"test_result", "test_execution", "artefact", "artefact_build"}
    assert set(row["test_result"]) == {"id", "created_at", "name", "category", "status"}
    assert row["test_result"]["name"].startswith("search-page-case-")
    assert row["test_result"]["category"] == "search-page-category"
    assert row["test_execution"]["environment"]["name"].startswith("search-page-env-")
    assert set(row["test_execution"]["environment"]) == {"name"}
    assert row["test_execution"]["test_plan"] == "search-page-plan"
    assert row["artefact"] == {
        "id": row["artefact"]["id"],
        "name": row["artefact"]["name"],
        "version": "1.2.3",
        "track": "stable",
        "family": "snap",
    }
    assert row["artefact"]["name"].startswith("search-page-artefact-")
    assert row["artefact_build"] == {"architecture": "arm64"}
    assert "private result comment" not in response.text
    assert "private result log" not in response.text
    assert statements
    assert all("io_log" not in statement for statement in statements)
    assert all("comment" not in statement for statement in statements)
    assert len(statements) == 1
