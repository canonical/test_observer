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
import re
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import Session

from test_observer.common.enums import Permission
from test_observer.data_access.models import IssueTestResultAttachment, TestResult
from tests.conftest import make_authenticated_request
from tests.data_generator import DataGenerator


def _create_search_result(
    generator: DataGenerator,
    execution_metadata: dict[str, list[str]] | None = None,
) -> int:
    suffix = uuid.uuid4().hex[:8]
    environment = generator.gen_environment()
    test_case = generator.gen_test_case(name=f"search_page_case_{suffix}")
    artefact = generator.gen_artefact(name=f"search_page_artefact_{suffix}")
    artefact_build = generator.gen_artefact_build(artefact)
    execution = generator.gen_test_execution(artefact_build, environment, execution_metadata=execution_metadata)
    result = generator.gen_test_result(test_case, execution)
    return result.id


def _count_statements(statements: list[str]) -> list[str]:
    return [
        statement
        for statement in statements
        if re.search(r"SELECT\s+count\(\*\).*\bFROM\s+test_result\b", statement, re.IGNORECASE | re.DOTALL)
    ]


def _selects_from(statements: list[str], table: str) -> list[str]:
    return [
        statement
        for statement in statements
        if re.search(rf"\bFROM\s+\"?{re.escape(table)}\"?\b", statement, re.IGNORECASE)
    ]


def _statements_referencing(statements: list[str], table: str) -> list[str]:
    return [statement for statement in statements if table in statement]


def test_search_page_includes_count_by_default(
    test_client: TestClient,
    generator: DataGenerator,
    db_session: Session,
):
    result_id = _create_search_result(generator)
    statements: list[str] = []
    connection = db_session.connection()

    def capture_statement(_conn: object, _cursor: object, sql: str, *_args: object) -> None:
        statements.append(sql)

    event.listen(connection, "before_cursor_execute", capture_statement)
    try:
        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-results/search-page"),
            Permission.view_test,
        )
    finally:
        event.remove(connection, "before_cursor_execute", capture_statement)

    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert set(data) == {"count", "limit", "offset", "rows"}
    row = next(row for row in data["rows"] if row["test_result"]["id"] == result_id)
    assert set(row["test_result"]) == {"id", "name", "category", "created_at", "template_id", "status", "issues"}
    assert set(row["test_execution"]) == {
        "id",
        "status",
        "environment",
        "test_plan",
        "rerun_is_requested",
        "execution_is_latest",
        "execution_metadata",
    }
    assert row["test_execution"]["rerun_is_requested"] is False
    assert row["test_execution"]["execution_is_latest"] is True
    assert row["test_execution"]["execution_metadata"] == []
    assert row["test_result"]["issues"] == []
    assert row["test_result"]["category"] == "camera"
    assert "io_log" not in row["test_result"]
    assert "comment" not in row["test_result"]
    page_query = next(statement for statement in statements if "FROM test_result ORDER BY" in statement)
    assert "test_result.io_log" not in page_query
    assert "test_result.comment" not in page_query
    assert len([statement for statement in statements if "FROM issue_test_result_attachment" in statement]) == 1
    assert len([statement for statement in statements if "FROM test_execution_rerun_request" in statement]) == 1
    assert len(_statements_referencing(statements, "test_execution_metadata_association_table")) == 1
    assert len(_statements_referencing(statements, "artefact_reviewers_association")) == 1
    assert set(row["artefact"]) == {"id", "name", "version", "track", "family", "stage", "archived", "reviewers"}
    assert row["artefact"]["reviewers"] == []
    artefact_load_query = next(
        statement for statement in statements if re.search(r"\bFROM\s+artefact\b", statement, re.IGNORECASE)
    )
    selected_columns = re.split(r"\bFROM\b", artefact_load_query, maxsplit=1, flags=re.IGNORECASE)[0]
    assert "artefact.stage" in selected_columns
    assert "artefact.archived" in selected_columns
    reviewer_load_query = _statements_referencing(statements, "artefact_reviewers_association")[0]
    assert "app_user.email" not in reviewer_load_query
    assert "app_user.name" in reviewer_load_query
    assert len(_count_statements(statements)) == 1

    openapi = test_client.app.openapi()
    components = openapi["components"]["schemas"]
    row_schema = components["SearchPageTableRow"]
    execution_schema_ref = row_schema["properties"]["test_execution"]["$ref"]
    execution_schema_name = execution_schema_ref.rsplit("/", maxsplit=1)[-1]
    assert set(components[execution_schema_name]["properties"]) == {
        "id",
        "status",
        "environment",
        "test_plan",
        "rerun_is_requested",
        "execution_is_latest",
        "execution_metadata",
    }
    artefact_schema_name = row_schema["properties"]["artefact"]["$ref"].rsplit("/", maxsplit=1)[-1]
    assert set(components[artefact_schema_name]["properties"]) == {
        "id",
        "name",
        "version",
        "track",
        "family",
        "stage",
        "archived",
        "reviewers",
    }
    test_result_schema_name = row_schema["properties"]["test_result"]["$ref"].rsplit("/", maxsplit=1)[-1]
    assert "issues" in components[test_result_schema_name]["properties"]


def test_search_page_can_skip_count_query(
    test_client: TestClient,
    generator: DataGenerator,
    db_session: Session,
):
    result_id = _create_search_result(generator)
    statements: list[str] = []

    def capture_statement(_conn: object, _cursor: object, sql: str, *_args: object) -> None:
        statements.append(sql)

    connection = db_session.connection()
    event.listen(connection, "before_cursor_execute", capture_statement)
    try:
        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-results/search-page", params={"include_count": "false"}),
            Permission.view_test,
        )
    finally:
        event.remove(connection, "before_cursor_execute", capture_statement)

    assert response.status_code == 200
    data = response.json()
    assert data["count"] is None
    assert any(row["test_result"]["id"] == result_id for row in data["rows"])
    assert _count_statements(statements) == []


def test_search_page_preserves_rerun_and_execution_metadata_filters(
    test_client: TestClient,
    generator: DataGenerator,
):
    environment_with_both = generator.gen_environment(name=f"search-page-{uuid.uuid4().hex[:8]}-both")
    environment_with_metadata = generator.gen_environment(name=f"search-page-{uuid.uuid4().hex[:8]}-metadata")
    environment_with_rerun = generator.gen_environment(name=f"search-page-{uuid.uuid4().hex[:8]}-rerun")
    test_case = generator.gen_test_case(name=f"search-page-{uuid.uuid4().hex[:8]}-case")
    artefact = generator.gen_artefact(name=f"search-page-{uuid.uuid4().hex[:8]}-artefact")
    artefact_build = generator.gen_artefact_build(artefact)
    metadata_category = f"search-page-{uuid.uuid4().hex[:8]}"
    metadata_value = f"search-page-{uuid.uuid4().hex[:8]}"

    execution_with_both = generator.gen_test_execution(
        artefact_build,
        environment_with_both,
        execution_metadata={metadata_category: [metadata_value]},
    )
    generator.gen_rerun_request(execution_with_both)
    result_with_both = generator.gen_test_result(test_case, execution_with_both)

    execution_with_metadata = generator.gen_test_execution(
        artefact_build,
        environment_with_metadata,
        execution_metadata={metadata_category: [metadata_value]},
    )
    result_with_metadata = generator.gen_test_result(test_case, execution_with_metadata)

    execution_with_rerun = generator.gen_test_execution(artefact_build, environment_with_rerun)
    generator.gen_rerun_request(execution_with_rerun)
    result_with_rerun = generator.gen_test_result(test_case, execution_with_rerun)

    encoded_category = base64.b64encode(metadata_category.encode()).decode()
    encoded_value = base64.b64encode(metadata_value.encode()).decode()
    response = make_authenticated_request(
        lambda: test_client.get(
            "/v1/test-results/search-page",
            params={
                "execution_metadata": f"{encoded_category}:{encoded_value}",
                "rerun_is_requested": "true",
                "limit": 1000,
            },
        ),
        Permission.view_test,
    )

    assert response.status_code == 200
    result_ids = {row["test_result"]["id"] for row in response.json()["rows"]}
    assert result_with_both.id in result_ids
    assert result_with_metadata.id not in result_ids
    assert result_with_rerun.id not in result_ids


def test_search_page_rows_return_filter_values_and_match_latest_rerun_predicates(
    test_client: TestClient,
    generator: DataGenerator,
):
    suffix = uuid.uuid4().hex[:8]
    reviewer = generator.gen_user(
        name=f"Search Reviewer {suffix}",
        launchpad_handle=f"search-reviewer-{suffix}",
        email=f"private-{suffix}@example.com",
    )
    artefact = generator.gen_artefact(
        name=f"search-page-values-{suffix}",
        stage="candidate",
        archived=True,
        reviewers=[reviewer],
    )
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment(name=f"search-page-values-{suffix}")
    test_case = generator.gen_test_case(name=f"search-page-values-{suffix}")
    long_value = "長い値 🔬 " + "x" * 170
    metadata = {
        "hardware/µ": [long_value, "GPU ⚡ — café"],
        "build.info": ["z-last", "a-first"],
    }
    older_execution = generator.gen_test_execution(
        artefact_build,
        environment,
        test_plan=f"search-page-plan-{suffix}",
    )
    latest_execution = generator.gen_test_execution(
        artefact_build,
        environment,
        test_plan=f"search-page-plan-{suffix}",
        execution_metadata=metadata,
    )
    generator.gen_rerun_request(older_execution)
    older_result = generator.gen_test_result(test_case, older_execution)
    latest_result = generator.gen_test_result(test_case, latest_execution)
    issue = generator.gen_issue(
        key=f"BUG-{suffix}",
        title=f"Search-safe issue label {suffix}",
    )
    db_session = generator.db_session
    db_session.add(IssueTestResultAttachment(test_result=latest_result, issue=issue))
    db_session.commit()

    encoded_category = base64.b64encode("hardware/µ".encode()).decode()
    encoded_value = base64.b64encode("GPU ⚡ — café".encode()).decode()
    response = make_authenticated_request(
        lambda: test_client.get(
            "/v1/test-results/search-page",
            params={
                "artefacts": artefact.name,
                "artefact_stages": "candidate",
                "artefact_is_archived": "true",
                "issues": issue.id,
                "reviewer_ids": reviewer.id,
                "rerun_is_requested": "true",
                "execution_is_latest": "true",
                "execution_metadata": f"{encoded_category}:{encoded_value}",
                "limit": 100,
            },
        ),
        Permission.view_test,
    )

    assert response.status_code == 200
    rows = response.json()["rows"]
    assert [row["test_result"]["id"] for row in rows] == [latest_result.id]
    row = rows[0]
    assert row["artefact"]["stage"] == "candidate"
    assert row["artefact"]["archived"] is True
    assert row["artefact"]["reviewers"] == [
        {"id": reviewer.id, "name": reviewer.name, "launchpad_handle": reviewer.launchpad_handle}
    ]
    assert "email" not in row["artefact"]["reviewers"][0]
    assert row["test_execution"]["rerun_is_requested"] is True
    assert row["test_execution"]["execution_is_latest"] is True
    assert row["test_result"]["issues"] == [{"id": issue.id, "key": issue.key, "title": issue.title}]
    assert row["test_execution"]["execution_metadata"] == [
        {"category": "build.info", "value": "a-first"},
        {"category": "build.info", "value": "z-last"},
        {"category": "hardware/µ", "value": "GPU ⚡ — café"},
        {"category": "hardware/µ", "value": long_value},
    ]

    older_response = make_authenticated_request(
        lambda: test_client.get(
            "/v1/test-results/search-page",
            params={
                "artefacts": artefact.name,
                "rerun_is_requested": "true",
                "execution_is_latest": "false",
            },
        ),
        Permission.view_test,
    )
    older_rows = older_response.json()["rows"]
    assert [row["test_result"]["id"] for row in older_rows] == [older_result.id]
    assert older_rows[0]["test_execution"]["rerun_is_requested"] is True
    assert older_rows[0]["test_execution"]["execution_is_latest"] is False

    no_rerun_response = make_authenticated_request(
        lambda: test_client.get(
            "/v1/test-results/search-page",
            params={"artefacts": artefact.name, "rerun_is_requested": "false"},
        ),
        Permission.view_test,
    )
    assert no_rerun_response.json()["rows"] == []


def test_search_page_batches_row_associations_without_changing_pagination(
    test_client: TestClient,
    generator: DataGenerator,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    user = generator.gen_user(name=f"Batched Reviewer {suffix}", email=f"private-{suffix}@example.com")
    artefact = generator.gen_artefact(name=f"search-page-batched-{suffix}", reviewers=[user])
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment(name=f"search-page-batched-{suffix}")
    test_case = generator.gen_test_case(name=f"search-page-batched-{suffix}")
    issues = [
        generator.gen_issue(key=f"BATCH-{suffix}-1", title="First batched issue"),
        generator.gen_issue(key=f"BATCH-{suffix}-2", title="Second batched issue"),
    ]
    result_ids = []
    for index in range(4):
        execution = generator.gen_test_execution(
            artefact_build,
            environment,
            execution_metadata={"batch-category": [f"value-{index}", "unicode-☃"]},
        )
        result = generator.gen_test_result(test_case, execution)
        result_ids.append(result.id)
        for issue in issues:
            db_session.add(IssueTestResultAttachment(test_result=result, issue=issue))
    db_session.commit()

    statements: list[str] = []

    def capture_statement(_conn: object, _cursor: object, sql: str, *_args: object) -> None:
        statements.append(sql)

    connection = db_session.connection()
    event.listen(connection, "before_cursor_execute", capture_statement)
    try:
        response = make_authenticated_request(
            lambda: test_client.get(
                "/v1/test-results/search-page",
                params={"artefacts": artefact.name, "limit": 10, "include_count": "false"},
            ),
            Permission.view_test,
        )
    finally:
        event.remove(connection, "before_cursor_execute", capture_statement)

    assert response.status_code == 200
    response_rows = response.json()["rows"]
    assert len(response_rows) == 4
    assert {row["test_result"]["id"] for row in response_rows} == set(result_ids)
    assert all(len(row["test_result"]["issues"]) == 2 for row in response_rows)
    assert all(len(row["test_execution"]["execution_metadata"]) == 2 for row in response_rows)
    assert all(len(row["artefact"]["reviewers"]) == 1 for row in response_rows)
    assert len(_selects_from(statements, "issue_test_result_attachment")) == 1
    assert len(_selects_from(statements, "issue")) == 1
    assert len(_statements_referencing(statements, "test_execution_metadata_association_table")) == 1
    assert len(_statements_referencing(statements, "artefact_reviewers_association")) == 1
    assert len(_selects_from(statements, "test_execution_rerun_request")) == 1
    assert _count_statements(statements) == []
    reviewer_statement = _statements_referencing(statements, "artefact_reviewers_association")[0]
    assert "app_user.email" not in reviewer_statement

    first_page = make_authenticated_request(
        lambda: test_client.get(
            "/v1/test-results/search-page",
            params={"artefacts": artefact.name, "limit": 1, "offset": 0},
        ),
        Permission.view_test,
    ).json()
    second_page = make_authenticated_request(
        lambda: test_client.get(
            "/v1/test-results/search-page",
            params={"artefacts": artefact.name, "limit": 1, "offset": 1},
        ),
        Permission.view_test,
    ).json()
    assert first_page["count"] == second_page["count"] == 4
    first_id = first_page["rows"][0]["test_result"]["id"]
    second_id = second_page["rows"][0]["test_result"]["id"]
    assert first_id != second_id


def test_search_page_details_endpoint_returns_modal_fields_only(
    test_client: TestClient,
    generator: DataGenerator,
    db_session: Session,
):
    result_id = _create_search_result(generator, execution_metadata={"hardware": ["search-page-device"]})
    test_result = db_session.get(TestResult, result_id)
    assert test_result is not None
    issue = generator.gen_issue(
        project=f"org/{uuid.uuid4().hex[:8]}",
        key=uuid.uuid4().hex[:8],
        title="Search page issue",
        labels=["table-label"],
    )
    db_session.add(IssueTestResultAttachment(test_result=test_result, issue=issue))
    db_session.commit()
    table_response = make_authenticated_request(
        lambda: test_client.get("/v1/test-results/search-page"),
        Permission.view_test,
    )
    assert table_response.status_code == 200
    table_data = table_response.json()
    table_row = next(row for row in table_data["rows"] if row["test_result"]["id"] == result_id)
    assert set(table_row["test_result"]) == {
        "id",
        "name",
        "category",
        "created_at",
        "template_id",
        "status",
        "issues",
    }
    assert set(table_row["test_execution"]) == {
        "id",
        "status",
        "environment",
        "test_plan",
        "rerun_is_requested",
        "execution_is_latest",
        "execution_metadata",
    }
    assert "io_log" not in table_row["test_result"]
    assert "comment" not in table_row["test_result"]

    filtered_response = make_authenticated_request(
        lambda: test_client.get("/v1/test-results/search-page", params={"issues": issue.id}),
        Permission.view_test,
    )
    assert filtered_response.status_code == 200
    assert any(row["test_result"]["id"] == result_id for row in filtered_response.json()["rows"])

    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/test-results/search-page/{result_id}"),
        Permission.view_test,
    )

    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"test_result", "test_execution", "artefact", "artefact_build"}
    assert set(data["test_result"]) == {
        "id",
        "name",
        "category",
        "template_id",
        "status",
        "io_log",
        "issues",
    }
    assert set(data["test_execution"]) == {
        "id",
        "status",
        "environment",
        "test_plan",
        "created_at",
        "execution_metadata",
    }
    assert set(data["artefact"]) == {"id", "name", "version", "track", "family"}
    assert set(data["artefact_build"]) == {"architecture"}
    assert data["test_execution"]["execution_metadata"] == {"hardware": ["search-page-device"]}
    issue_data = data["test_result"]["issues"][0]["issue"]
    assert issue_data["id"] == issue.id
    assert issue_data["title"] == "Search page issue"
    assert issue_data["source"] == "github"
    assert issue_data["status"] == "open"
    assert issue_data["url"] == issue.url
    assert set(issue_data) == {"id", "source", "project", "key", "title", "status", "url"}
    assert "attachment_rule" not in data["test_result"]["issues"][0]

    schemas = test_client.app.openapi()["components"]["schemas"]
    issue_schema = schemas["SearchPageDetailsIssue"]
    source_schema = schemas[issue_schema["properties"]["source"]["$ref"].rsplit("/", maxsplit=1)[-1]]
    status_schema = schemas[issue_schema["properties"]["status"]["$ref"].rsplit("/", maxsplit=1)[-1]]
    assert source_schema["enum"] == ["jira", "github", "launchpad"]
    assert status_schema["enum"] == ["unknown", "open", "closed"]
    assert issue_schema["properties"]["url"]["format"] == "uri"


def test_search_page_details_endpoint_returns_not_found_for_missing_result(
    test_client: TestClient,
):
    response = make_authenticated_request(
        lambda: test_client.get("/v1/test-results/search-page/999999999"),
        Permission.view_test,
    )
    assert response.status_code == 404
