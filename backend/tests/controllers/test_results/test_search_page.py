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

import base64
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from test_observer.common.config import MAX_RESULT_PAGE_LIMIT
from test_observer.common.enums import Permission
from test_observer.data_access.models import Environment, IssueTestResultAttachment, TestCase, TestResult
from test_observer.data_access.models_enums import FamilyName, TestExecutionStatus, TestResultStatus
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


def test_search_page_details_endpoint_requires_permission_and_valid_ids(
    test_client: TestClient,
    generator: DataGenerator,
):
    result = _create_test_result(generator)
    endpoint = f"{SEARCH_PAGE_ENDPOINT}/{result.id}"

    assert test_client.get(endpoint).status_code == 403
    with override_permissions():
        assert test_client.get(endpoint).status_code == 403
    with override_permissions(Permission.view_test):
        assert test_client.get(endpoint).status_code == 200
        assert test_client.get(f"{SEARCH_PAGE_ENDPOINT}/0").status_code == 422
        assert test_client.get(f"{SEARCH_PAGE_ENDPOINT}/999999999").status_code == 404


def test_search_page_details_are_lazy_and_return_only_modal_data(
    test_client: TestClient,
    db_session: Session,
    generator: DataGenerator,
):
    result, issue_id, _reviewer_id, _unique = _create_advanced_search_result(generator)
    io_log = "<script>globalThis.pwned = true</script>\n" + "x" * 100_000
    result.io_log = io_log
    db_session.flush()

    with override_permissions(Permission.view_test):
        table_response = test_client.get(SEARCH_PAGE_ENDPOINT)
        details_response = test_client.get(f"{SEARCH_PAGE_ENDPOINT}/{result.id}")

    assert table_response.status_code == 200
    table_body = table_response.json()
    row = next(row for row in table_body["test_results"] if row["test_result"]["id"] == result.id)
    assert set(row["test_result"]) == {"id", "created_at", "name", "category", "status"}
    assert "io_log" not in table_response.text
    assert "comment" not in table_response.text
    assert io_log not in table_response.text

    assert details_response.status_code == 200
    body = details_response.json()
    assert set(body) == {"test_result", "test_execution", "artefact", "artefact_build"}
    assert set(body["test_result"]) == {
        "id",
        "name",
        "category",
        "template_id",
        "status",
        "io_log",
        "issues",
    }
    assert body["test_result"]["io_log"] == io_log
    assert body["test_execution"]["execution_metadata"] == {
        "device:🌱": ["arm64, revision: 1"],
    }
    issue = body["test_result"]["issues"][0]["issue"]
    assert issue["id"] == issue_id
    assert set(issue) == {"id", "source", "project", "key", "title", "status", "url"}
    assert "attachment_rule" not in body["test_result"]["issues"][0]


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


def _encoded_metadata_part(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def _create_advanced_search_result(generator: DataGenerator) -> tuple[TestResult, int, int, str]:
    unique = uuid4().hex
    user = generator.gen_user()
    artefact = generator.gen_artefact(
        name=f"advanced-search-artefact-{unique}",
        stage="",
        archived=True,
        reviewers=[user],
    )
    build = generator.gen_artefact_build(artefact, architecture="amd64")
    environment = generator.gen_environment(name=f"advanced-search-env-{unique}")
    plan = f"advanced-search-plan-{unique}"
    test_case = generator.gen_test_case(name=f"advanced-search-case-{unique}", template_id=f"template-{unique}")
    execution = generator.gen_test_execution(
        build,
        environment,
        test_plan=plan,
        status=TestExecutionStatus.PASSED,
        execution_metadata={"device:🌱": ["arm64, revision: 1"]},
    )
    result = generator.gen_test_result(test_case, execution)
    issue = generator.gen_issue(key=f"advanced-{unique}")
    generator.db_session.add(IssueTestResultAttachment(issue=issue, test_result=result))
    generator.gen_rerun_request(execution)
    newer_execution = generator.gen_test_execution(
        build,
        environment,
        test_plan=plan,
        status=TestExecutionStatus.FAILED,
    )
    generator.gen_test_result(test_case, newer_execution)
    generator.db_session.flush()
    return result, issue.id, user.id, unique


def test_search_page_supports_all_advanced_filters_and_empty_stage(
    test_client: TestClient,
    generator: DataGenerator,
):
    result, issue_id, reviewer_id, unique = _create_advanced_search_result(generator)
    metadata = f"{_encoded_metadata_part('device:🌱')}:{_encoded_metadata_part('arm64, revision: 1')}"
    params = [
        ("artefact_stages", ""),
        ("artefact_is_archived", "true"),
        ("test_execution_statuses", "PASSED"),
        ("rerun_is_requested", "true"),
        ("execution_is_latest", "false"),
        ("template_ids", f"template-{unique}"),
        ("issues", str(issue_id)),
        ("reviewer_ids", str(reviewer_id)),
        ("execution_metadata", metadata),
    ]

    with override_permissions(Permission.view_test):
        response = test_client.get(SEARCH_PAGE_ENDPOINT, params=params)
        without_empty_stage = test_client.get(
            SEARCH_PAGE_ENDPOINT,
            params=[(key, value) for key, value in params if key != "artefact_stages"],
        )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert [row["test_result"]["id"] for row in response.json()["test_results"]] == [result.id]
    assert without_empty_stage.status_code == 200
    assert without_empty_stage.json()["count"] == 1


def test_search_page_empty_stage_is_distinct_from_omitted_filter(
    test_client: TestClient,
    generator: DataGenerator,
):
    empty_stage = _create_advanced_search_result(generator)[0]
    nonempty_stage = _create_search_result(generator, name=f"stage-not-empty-{uuid4().hex}")

    with override_permissions(Permission.view_test):
        omitted = test_client.get(SEARCH_PAGE_ENDPOINT)
        explicit_empty = test_client.get(SEARCH_PAGE_ENDPOINT, params=[("artefact_stages", "")])

    assert omitted.status_code == explicit_empty.status_code == 200
    assert omitted.json()["count"] == 3
    assert explicit_empty.json()["count"] == 2
    assert empty_stage.id in {row["test_result"]["id"] for row in explicit_empty.json()["test_results"]}
    assert nonempty_stage.id not in {row["test_result"]["id"] for row in explicit_empty.json()["test_results"]}


def test_search_page_id_filters_support_positive_any_none_and_exclusive_sentinels(
    test_client: TestClient,
    generator: DataGenerator,
):
    target, issue_id, reviewer_id, _ = _create_advanced_search_result(generator)
    no_attachment = _create_search_result(generator, name=f"no-issue-{uuid4().hex}")
    no_reviewer = _create_search_result(generator, name=f"no-reviewer-{uuid4().hex}")

    with override_permissions(Permission.view_test):
        issue_positive = test_client.get(SEARCH_PAGE_ENDPOINT, params={"issues": str(issue_id)})
        issue_any = test_client.get(SEARCH_PAGE_ENDPOINT, params={"issues": "any"})
        issue_none = test_client.get(SEARCH_PAGE_ENDPOINT, params={"issues": "none"})
        reviewer_positive = test_client.get(SEARCH_PAGE_ENDPOINT, params={"reviewer_ids": str(reviewer_id)})
        reviewer_any = test_client.get(SEARCH_PAGE_ENDPOINT, params={"reviewer_ids": "any"})
        reviewer_none = test_client.get(SEARCH_PAGE_ENDPOINT, params={"reviewer_ids": "none"})
        alias = test_client.get(SEARCH_PAGE_ENDPOINT, params={"assignee_ids": str(reviewer_id)})

    assert issue_positive.json()["count"] == 1
    assert [row["test_result"]["id"] for row in issue_positive.json()["test_results"]] == [target.id]
    assert issue_any.json()["count"] == 1
    assert issue_none.json()["count"] == 3
    assert reviewer_positive.json()["count"] == 2
    assert reviewer_any.json()["count"] == 2
    assert reviewer_none.json()["count"] == 2
    assert no_attachment.id in {row["test_result"]["id"] for row in issue_none.json()["test_results"]}
    assert no_reviewer.id in {row["test_result"]["id"] for row in reviewer_none.json()["test_results"]}
    assert alias.status_code == 422


@pytest.mark.parametrize(
    "params",
    [
        [("issues", "0")],
        [("issues", "-1")],
        [("issues", "9007199254740992")],
        [("reviewer_ids", "2147483648")],
        [("issues", "any"), ("issues", "1")],
        [("issues", "any"), ("issues", "none")],
        [("reviewer_ids", "none"), ("reviewer_ids", "2")],
    ],
)
def test_search_page_rejects_malformed_id_filter_values(
    test_client: TestClient,
    params: list[tuple[str, str]],
):
    with override_permissions(Permission.view_test):
        response = test_client.get(SEARCH_PAGE_ENDPOINT, params=params)
    assert response.status_code == 422


@pytest.mark.parametrize(
    "params",
    [
        [("artefact_is_archived", "TRUE")],
        [("rerun_is_requested", "1")],
        [("execution_is_latest", "yes")],
        [("artefact_is_archived", "true"), ("artefact_is_archived", "false")],
    ],
)
def test_search_page_rejects_noncanonical_or_duplicate_boolean_filters(
    test_client: TestClient,
    params: list[tuple[str, str]],
):
    with override_permissions(Permission.view_test):
        response = test_client.get(SEARCH_PAGE_ENDPOINT, params=params)
    assert response.status_code == 422


def test_search_page_boolean_false_values_are_applied(
    test_client: TestClient,
    generator: DataGenerator,
):
    _create_search_result(generator, name=f"unarchived-{uuid4().hex}")
    _create_advanced_search_result(generator)
    with override_permissions(Permission.view_test):
        response = test_client.get(
            SEARCH_PAGE_ENDPOINT,
            params={"artefact_is_archived": "false", "rerun_is_requested": "false"},
        )
    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_search_page_execution_metadata_values_are_or_within_category_and_and_across_categories(
    test_client: TestClient,
    generator: DataGenerator,
):
    matched_ids: set[int] = set()
    for device, os_name in (("arm64", "ubuntu"), ("x86_64", "ubuntu")):
        artefact = generator.gen_artefact(name=f"metadata-{uuid4().hex}")
        build = generator.gen_artefact_build(artefact)
        environment = generator.gen_environment(name=f"metadata-env-{uuid4().hex}")
        execution = generator.gen_test_execution(
            build,
            environment,
            execution_metadata={"device": [device], "os": [os_name]},
        )
        case = generator.gen_test_case(name=f"metadata-case-{uuid4().hex}")
        matched_ids.add(generator.gen_test_result(case, execution).id)
    artefact = generator.gen_artefact(name=f"metadata-excluded-{uuid4().hex}")
    build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment(name=f"metadata-env-{uuid4().hex}")
    execution = generator.gen_test_execution(
        build,
        environment,
        execution_metadata={"device": ["arm64"], "os": ["debian"]},
    )
    generator.gen_test_result(generator.gen_test_case(name=f"metadata-case-{uuid4().hex}"), execution)

    pairs = [
        f"{_encoded_metadata_part('device')}:{_encoded_metadata_part('arm64')}",
        f"{_encoded_metadata_part('device')}:{_encoded_metadata_part('x86_64')}",
        f"{_encoded_metadata_part('os')}:{_encoded_metadata_part('ubuntu')}",
    ]
    with override_permissions(Permission.view_test):
        response = test_client.get(SEARCH_PAGE_ENDPOINT, params=[("execution_metadata", item) for item in pairs])
    assert response.status_code == 200
    assert response.json()["count"] == 2
    assert {row["test_result"]["id"] for row in response.json()["test_results"]} == matched_ids


@pytest.mark.parametrize(
    "pair",
    [
        "not-base64",
        "e30=",
        ":",
        f"{_encoded_metadata_part('')}:eA==",
        f"{_encoded_metadata_part('category')}:",
        f"{_encoded_metadata_part('category')}:{_encoded_metadata_part('é' * 201)}",
        "//46:eA==",  # valid Base64 bytes, but not UTF-8
    ],
)
def test_search_page_rejects_malformed_metadata_pairs(test_client: TestClient, pair: str):
    with override_permissions(Permission.view_test):
        response = test_client.get(SEARCH_PAGE_ENDPOINT, params={"execution_metadata": pair})
    assert response.status_code == 422


def test_search_page_advanced_filtered_count_offsets_and_order_are_stable(
    test_client: TestClient,
    generator: DataGenerator,
):
    timestamp = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
    results = []
    for index in range(5):
        environment = generator.gen_environment(name=f"advanced-page-env-{uuid4().hex}")
        artefact = generator.gen_artefact(name=f"advanced-page-{index}-{uuid4().hex}", stage="candidate")
        build = generator.gen_artefact_build(artefact)
        execution = generator.gen_test_execution(build, environment, status=TestExecutionStatus.PASSED)
        result = generator.gen_test_result(generator.gen_test_case(name=f"advanced-page-case-{uuid4().hex}"), execution)
        result.created_at = timestamp
        results.append(result)
    environment = generator.gen_environment(name=f"advanced-page-env-{uuid4().hex}")
    artefact = generator.gen_artefact(name=f"advanced-page-excluded-{uuid4().hex}", stage="stable")
    build = generator.gen_artefact_build(artefact)
    execution = generator.gen_test_execution(build, environment, status=TestExecutionStatus.PASSED)
    generator.gen_test_result(generator.gen_test_case(name=f"advanced-page-case-{uuid4().hex}"), execution)
    generator.db_session.flush()

    params = [("artefact_stages", "candidate"), ("test_execution_statuses", "PASSED"), ("limit", "2")]
    with override_permissions(Permission.view_test):
        pages = [
            test_client.get(SEARCH_PAGE_ENDPOINT, params=[*params, ("offset", str(offset))]) for offset in (0, 2, 4)
        ]
    assert all(page.status_code == 200 for page in pages)
    bodies = [page.json() for page in pages]
    assert [body["count"] for body in bodies] == [5, 5, 5]
    ids = [row["test_result"]["id"] for body in bodies for row in body["test_results"]]
    assert ids == sorted((result.id for result in results), reverse=True)
    assert [len(body["test_results"]) for body in bodies] == [2, 2, 1]


def test_search_page_openapi_documents_all_advanced_query_parameters(test_client: TestClient):
    response = test_client.get("/openapi.json")
    assert response.status_code == 200
    operation = response.json()["paths"][SEARCH_PAGE_ENDPOINT]["get"]
    parameters = {parameter["name"]: parameter for parameter in operation["parameters"]}
    advanced = {
        "artefact_stages",
        "artefact_is_archived",
        "test_execution_statuses",
        "rerun_is_requested",
        "execution_is_latest",
        "template_ids",
        "issues",
        "reviewer_ids",
        "execution_metadata",
    }
    assert advanced <= parameters.keys()
    assert "empty stage" in parameters["artefact_stages"]["description"]
    assert "Base64 UTF-8" in parameters["execution_metadata"]["description"]


def test_search_page_openapi_documents_lazy_details_endpoint(test_client: TestClient):
    response = test_client.get("/openapi.json")
    assert response.status_code == 200
    openapi = response.json()
    path = f"{SEARCH_PAGE_ENDPOINT}/{{test_result_id}}"
    operation = openapi["paths"][path]["get"]
    path_parameter = next(parameter for parameter in operation["parameters"] if parameter["in"] == "path")
    assert path_parameter["name"] == "test_result_id"
    assert path_parameter["schema"]["exclusiveMinimum"] == 0
    assert (
        operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/SearchPageDetailsResponse"
    )
