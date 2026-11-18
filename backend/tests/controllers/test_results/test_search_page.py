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

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from test_observer.common.config import MAX_RESULT_PAGE_LIMIT
from test_observer.common.enums import Permission
from test_observer.data_access.models import Environment, TestCase, TestResult
from test_observer.data_access.models_enums import FamilyName, TestResultStatus
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


def _create_search_result(
    generator: DataGenerator,
    *,
    name: str,
    family: FamilyName = FamilyName.snap,
    version: str = "1.2.3",
    track: str = "stable",
    environment_name: str = "search-env",
    test_case_name: str = "search-case",
    test_plan_name: str = "search-plan",
    status: TestResultStatus = TestResultStatus.PASSED,
    created_at: datetime | None = None,
) -> TestResult:
    environment = generator.db_session.query(Environment).filter_by(name=environment_name, architecture="amd64").first()
    if environment is None:
        environment = generator.gen_environment(name=environment_name)
    test_case = generator.db_session.query(TestCase).filter_by(name=test_case_name).first()
    if test_case is None:
        test_case = generator.gen_test_case(name=test_case_name)
    artefact = generator.gen_artefact(
        name=name,
        family=family,
        version=version,
        track=track,
    )
    artefact_build = generator.gen_artefact_build(artefact, architecture="arm64")
    test_execution = generator.gen_test_execution(
        artefact_build,
        environment,
        test_plan=test_plan_name,
    )
    result = generator.gen_test_result(test_case, test_execution, status=status)
    if created_at is not None:
        result.created_at = created_at
    return result


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
    assert body["count"] == 1
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
        {"include_count": "not-a-boolean"},
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
        responses = [
            test_client.get(SEARCH_PAGE_ENDPOINT, params={"limit": 2, "offset": offset}) for offset in (0, 2, 4)
        ]

    assert all(response.status_code == 200 for response in responses)
    pages = [response.json() for response in responses]
    assert [body["limit"] for body in pages] == [2, 2, 2]
    assert [body["offset"] for body in pages] == [0, 2, 4]
    assert [body["count"] for body in pages] == [5, 5, 5]
    page_ids = [row["test_result"]["id"] for body in pages for row in body["test_results"]]
    assert page_ids == sorted((result.id for result in results), reverse=True)
    assert [len(body["test_results"]) for body in pages] == [2, 2, 1]


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
    assert body["count"] == 1
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
    assert len(statements) == 2
    count_statement = next(statement for statement in statements if "count(" in statement)
    page_statement = next(statement for statement in statements if "count(" not in statement)
    assert "from test_result" in count_statement
    assert " join " not in count_statement
    assert "io_log" not in page_statement
    assert "comment" not in page_statement


def test_search_page_count_is_zero_for_empty_result_set(test_client: TestClient):
    with override_permissions(Permission.view_test):
        response = test_client.get(SEARCH_PAGE_ENDPOINT)

    assert response.status_code == 200
    assert response.json() == {
        "count": 0,
        "limit": 50,
        "offset": 0,
        "test_results": [],
    }


def test_search_page_can_omit_count(
    test_client: TestClient,
    db_session: Session,
    generator: DataGenerator,
):
    _create_test_result(generator)
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
            response = test_client.get(SEARCH_PAGE_ENDPOINT, params={"include_count": "false"})
    finally:
        event.remove(connection, "before_cursor_execute", capture_select)

    assert response.status_code == 200
    assert response.json()["count"] is None
    assert len(statements) == 1
    assert all("count(" not in statement for statement in statements)


def test_search_page_count_is_a_separate_unjoined_query(
    test_client: TestClient,
    db_session: Session,
    generator: DataGenerator,
):
    results = [_create_test_result(generator) for _ in range(3)]
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
            response = test_client.get(
                SEARCH_PAGE_ENDPOINT,
                params={"limit": 1, "offset": 1},
            )
    finally:
        event.remove(connection, "before_cursor_execute", capture_select)

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == len(results)
    assert len(body["test_results"]) == 1
    count_statement = next(statement for statement in statements if "count(" in statement)
    page_statement = next(statement for statement in statements if "count(" not in statement)
    assert "from test_result" in count_statement
    assert " join " not in count_statement
    assert "limit" not in count_statement
    assert "offset" not in count_statement
    assert "limit" in page_statement
    assert "offset" in page_statement


def test_search_page_include_count_must_be_boolean(test_client: TestClient):
    with override_permissions(Permission.view_test):
        response = test_client.get(SEARCH_PAGE_ENDPOINT, params={"include_count": "sometimes"})

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("filter_name", "matching_value", "nonmatching_value"),
    [
        ("families", "snap", "charm"),
        ("test_result_statuses", "PASSED", "FAILED"),
        ("artefacts", "search-filter-artefact", "other-artefact"),
        ("artefact_versions", "7.2.1", "7.2.2"),
        ("artefact_tracks", "edge", "stable"),
        ("environments", "search-filter-env", "other-env"),
        ("test_cases", "search-filter-case", "other-case"),
        ("test_plans", "search-filter-plan", "other-plan"),
    ],
)
def test_search_page_filters_each_supported_field_exactly(
    test_client: TestClient,
    generator: DataGenerator,
    filter_name: str,
    matching_value: str,
    nonmatching_value: str,
):
    _create_search_result(
        generator,
        name="search-filter-artefact",
        version="7.2.1",
        track="edge",
        environment_name="search-filter-env",
        test_case_name="search-filter-case",
        test_plan_name="search-filter-plan",
    )

    with override_permissions(Permission.view_test):
        matched = test_client.get(SEARCH_PAGE_ENDPOINT, params={filter_name: matching_value})
        unmatched = test_client.get(SEARCH_PAGE_ENDPOINT, params={filter_name: nonmatching_value})

    assert matched.status_code == 200
    assert matched.json()["count"] == 1
    assert len(matched.json()["test_results"]) == 1
    assert unmatched.status_code == 200
    assert unmatched.json()["count"] == 0
    assert unmatched.json()["test_results"] == []


def test_search_page_combines_repeated_values_with_or_and_fields_with_and(
    test_client: TestClient,
    generator: DataGenerator,
):
    matched_ids = {
        _create_search_result(
            generator,
            name="search-combined-snap-pass",
            environment_name="search-combined-env",
            status=TestResultStatus.PASSED,
        ).id,
        _create_search_result(
            generator,
            name="search-combined-deb-fail",
            family=FamilyName.deb,
            environment_name="search-combined-env",
            status=TestResultStatus.FAILED,
        ).id,
    }
    _create_search_result(
        generator,
        name="search-combined-snap-skip",
        environment_name="search-other-env",
        status=TestResultStatus.SKIPPED,
    )

    params = [
        ("families", "snap"),
        ("families", "deb"),
        ("test_result_statuses", "PASSED"),
        ("test_result_statuses", "FAILED"),
        ("environments", "search-combined-env"),
    ]
    with override_permissions(Permission.view_test):
        response = test_client.get(SEARCH_PAGE_ENDPOINT, params=params)
        different_field = test_client.get(SEARCH_PAGE_ENDPOINT, params=[*params, ("test_plans", "wrong-plan")])

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert {row["test_result"]["id"] for row in body["test_results"]} == matched_ids
    assert different_field.status_code == 200
    assert different_field.json()["count"] == 0


def test_search_page_date_bounds_are_inclusive_utc_timestamps(
    test_client: TestClient,
    generator: DataGenerator,
):
    lower = datetime(2026, 2, 1, 0, 0, tzinfo=UTC)
    upper = datetime(2026, 2, 2, 0, 0, tzinfo=UTC)
    included = [
        _create_search_result(generator, name=f"date-bound-{index}", created_at=timestamp)
        for index, timestamp in enumerate(
            (
                datetime(2026, 1, 31, 23, 59, tzinfo=UTC),
                lower,
                datetime(2026, 2, 1, 12, 0, tzinfo=UTC),
                upper,
                datetime(2026, 2, 2, 0, 1, tzinfo=UTC),
            )
        )
    ]
    params = {
        "from_date": lower.isoformat().replace("+00:00", "Z"),
        "until_date": upper.isoformat().replace("+00:00", "Z"),
    }

    with override_permissions(Permission.view_test):
        response = test_client.get(SEARCH_PAGE_ENDPOINT, params=params)

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 3
    assert {row["test_result"]["id"] for row in body["test_results"]} == {result.id for result in included[1:4]}


@pytest.mark.parametrize(
    "params",
    [
        {"families": "unknown-family"},
        {"test_result_statuses": "UNKNOWN"},
        {"artefacts": ""},
        {"artefacts": "   "},
        {"from_date": "not-a-date"},
        {"from_date": "2026-01-02T03:04:05"},
        {"from_date": "2026-02-02T00:00:00Z", "until_date": "2026-02-01T00:00:00Z"},
        {"unsupported_filter": "value"},
        [("from_date", "2026-01-01T00:00:00Z"), ("from_date", "2026-01-02T00:00:00Z")],
    ],
)
def test_search_page_rejects_invalid_or_unsupported_filter_values(
    test_client: TestClient,
    params: dict[str, str] | list[tuple[str, str]],
):
    with override_permissions(Permission.view_test):
        response = test_client.get(SEARCH_PAGE_ENDPOINT, params=params)

    assert response.status_code == 422


def test_search_page_filtered_count_matches_offsets_and_stable_order(
    test_client: TestClient,
    generator: DataGenerator,
):
    timestamp = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)
    results = [
        _create_search_result(
            generator,
            name=f"filtered-page-{index}",
            track="filtered-track",
            created_at=timestamp,
        )
        for index in range(5)
    ]
    _create_search_result(generator, name="filtered-page-excluded", track="other-track", created_at=timestamp)

    with override_permissions(Permission.view_test):
        responses = [
            test_client.get(
                SEARCH_PAGE_ENDPOINT,
                params={"artefact_tracks": "filtered-track", "limit": 2, "offset": offset},
            )
            for offset in (0, 2, 4)
        ]

    assert all(response.status_code == 200 for response in responses)
    pages = [response.json() for response in responses]
    assert [page["count"] for page in pages] == [5, 5, 5]
    assert [len(page["test_results"]) for page in pages] == [2, 2, 1]
    returned_ids = [row["test_result"]["id"] for page in pages for row in page["test_results"]]
    assert returned_ids == sorted((result.id for result in results), reverse=True)
