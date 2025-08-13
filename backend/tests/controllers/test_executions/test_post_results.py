# Copyright (C) 2023 Canonical Ltd.
#
# This file is part of Test Observer Backend.
#
# Test Observer Backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# Test Observer Backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import pytest
from fastapi.testclient import TestClient

from test_observer.data_access.models import TestExecution, TestResult
from tests.asserts import assert_fails_validation
from tests.data_generator import DataGenerator

maximum_result = {
    "name": "camera detect",
    "status": "PASSED",
    "template_id": "template",
    "category": "camera",
    "comment": "No comment",
    "io_log": "test io log",
}

minimum_result = {"name": "test", "status": "FAILED"}


def _assert_results(request: list[dict[str, str]], results: list[TestResult]) -> None:
    assert len(request) == len(results)
    for submitted, expected in zip(request, results, strict=True):
        assert expected.test_case.name == submitted["name"]
        assert expected.status == submitted["status"]
        assert expected.test_case.template_id == submitted.get("template_id", "")
        assert expected.test_case.category == submitted.get("category", "")
        assert expected.comment == submitted.get("comment", "")
        assert expected.io_log == submitted.get("io_log", "")


def test_missing_test_execution(test_client: TestClient):
    response = test_client.post("/v1/test-executions/1/test-results", json=[])
    assert response.status_code == 404


def test_one_full_test_result(test_client: TestClient, test_execution: TestExecution):
    response = test_client.post(
        f"/v1/test-executions/{test_execution.id}/test-results", json=[maximum_result]
    )

    assert response.status_code == 200
    _assert_results([maximum_result], test_execution.test_results)


def test_one_minimum_result(test_client: TestClient, test_execution: TestExecution):
    response = test_client.post(
        f"/v1/test-executions/{test_execution.id}/test-results", json=[minimum_result]
    )

    assert response.status_code == 200
    _assert_results([minimum_result], test_execution.test_results)


@pytest.mark.parametrize("field", ["name", "status"])
def test_required_fields(
    test_client: TestClient, test_execution: TestExecution, field: str
):
    result = minimum_result.copy()
    result.pop(field)
    response = test_client.post(
        f"/v1/test-executions/{test_execution.id}/test-results", json=[result]
    )

    assert_fails_validation(response, field, "missing")


def test_batch_request(test_client: TestClient, test_execution: TestExecution):
    request = [
        {**maximum_result, "name": "test 1", "status": "PASSED"},
        {**maximum_result, "name": "test 2", "status": "FAILED"},
        {**maximum_result, "name": "test 3", "status": "SKIPPED"},
    ]

    response = test_client.post(
        f"/v1/test-executions/{test_execution.id}/test-results",
        json=request,
    )

    assert response.status_code == 200
    _assert_results(request, test_execution.test_results)


def test_multiple_batch_requests(
    test_client: TestClient, test_execution: TestExecution
):
    request1 = [
        {**maximum_result, "name": "test 1", "status": "PASSED"},
        {**maximum_result, "name": "test 2", "status": "FAILED"},
        {**maximum_result, "name": "test 3", "status": "SKIPPED"},
    ]

    request2 = [
        {**maximum_result, "name": "test 4", "status": "PASSED"},
        {**maximum_result, "name": "test 5", "status": "FAILED"},
        {**maximum_result, "name": "test 6", "status": "SKIPPED"},
    ]

    test_client.post(
        f"/v1/test-executions/{test_execution.id}/test-results", json=request1
    )
    test_client.post(
        f"/v1/test-executions/{test_execution.id}/test-results", json=request2
    )

    _assert_results([*request1, *request2], test_execution.test_results)


def test_overwrites_result_if_matching_case_name(
    test_client: TestClient, test_execution: TestExecution
):
    request1 = [{**minimum_result, "name": "same", "status": "FAILED"}]
    request2 = [{**minimum_result, "name": "same", "status": "PASSED"}]

    test_client.post(
        f"/v1/test-executions/{test_execution.id}/test-results", json=request1
    )
    test_client.post(
        f"/v1/test-executions/{test_execution.id}/test-results", json=request2
    )

    _assert_results(request2, test_execution.test_results)


def test_apply_test_result_attachment_rules(
    test_client: TestClient, test_execution: TestExecution, generator: DataGenerator
):
    issue = generator.gen_issue()

    attachment_rule_response = test_client.post(
        f"/v1/issues/{issue.id}/attachment-rules",
        json={
            "enabled": True,
            "families": [test_execution.artefact_build.artefact.family],
        },
    )
    attachment_rule_id = attachment_rule_response.json()["id"]

    test_client.post(
        f"/v1/test-executions/{test_execution.id}/test-results", json=[minimum_result]
    )

    assert test_execution.test_results[0].issue_attachments[0].issue_id == issue.id
    assert (
        test_execution.test_results[0].issue_attachments[0].attachment_rule_id
        == attachment_rule_id
    )
