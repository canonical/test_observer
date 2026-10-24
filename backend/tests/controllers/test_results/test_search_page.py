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
    assert set(row["test_result"]) == {"id", "name", "category", "created_at", "template_id", "status"}
    assert set(row["test_execution"]) == {"id", "status", "environment", "test_plan"}
    assert row["test_result"]["category"] == "camera"
    assert "io_log" not in row["test_result"]
    assert "comment" not in row["test_result"]
    page_query = next(statement for statement in statements if "FROM test_result ORDER BY" in statement)
    assert "test_result.io_log" not in page_query
    assert "test_result.comment" not in page_query
    assert not any("FROM issue_test_result_attachment" in statement for statement in statements)
    assert not any("FROM test_execution_rerun_request" in statement for statement in statements)
    assert not any("FROM test_execution_metadata" in statement for statement in statements)
    assert set(row["artefact"]) == {"id", "name", "version", "track", "family"}
    assert not any("FROM artefact_reviewers_association" in statement for statement in statements)
    artefact_load_query = next(
        statement for statement in statements if re.search(r"\bFROM\s+artefact\b", statement, re.IGNORECASE)
    )
    selected_columns = re.split(r"\bFROM\b", artefact_load_query, maxsplit=1, flags=re.IGNORECASE)[0]
    assert "artefact.stage" not in selected_columns
    assert "artefact.archived" not in selected_columns
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
    }


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
    assert set(table_row["test_result"]) == {"id", "name", "category", "created_at", "template_id", "status"}
    assert set(table_row["test_execution"]) == {"id", "status", "environment", "test_plan"}
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
    assert issue_data["url"] == issue.url
    assert set(issue_data) == {"id", "source", "project", "key", "title", "status", "url"}
    assert "attachment_rule" not in data["test_result"]["issues"][0]


def test_search_page_details_endpoint_returns_not_found_for_missing_result(
    test_client: TestClient,
):
    response = make_authenticated_request(
        lambda: test_client.get("/v1/test-results/search-page/999999999"),
        Permission.view_test,
    )
    assert response.status_code == 404
