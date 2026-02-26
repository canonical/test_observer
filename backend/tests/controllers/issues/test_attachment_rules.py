# Copyright 2025 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from fastapi.testclient import TestClient
import pytest

from tests.conftest import make_authenticated_request
from tests.data_generator import DataGenerator
from sqlalchemy.orm import Session
from test_observer.common.permissions import Permission
from test_observer.data_access.models import (
    IssueTestResultAttachmentRuleExecutionMetadata,
    IssueTestResultAttachmentRule,
)
from test_observer.data_access.models_enums import TestResultStatus
from test_observer.controllers.issues.attachment_rules_logic import (
    apply_test_result_attachment_rules,
)
from test_observer.data_access.models import TestExecution

issue_endpoint = "/v1/issues/{issue_id}"
post_endpoint = issue_endpoint + "/attachment-rules"
patch_endpoint = post_endpoint + "/{attachment_rule_id}"
delete_endpoint = patch_endpoint


def auth_request(method: str, test_client: TestClient, endpoint: str, **kwargs):
    return make_authenticated_request(
        lambda: getattr(test_client, method)(endpoint, **kwargs),
        Permission.change_attachment_rule,
    )


@pytest.fixture
def post_attachment_rule():
    return {
        "enabled": True,
        "families": ["charm"],
        "environment_names": ["environment-1"],
        "test_case_names": ["test-case-1"],
        "template_ids": ["template-id-1"],
        "execution_metadata": {"category-1": ["value-1", "value-2"]},
    }


def _assert_attachment_rule_response(
    json: dict,
    model: IssueTestResultAttachmentRule | None,
) -> None:
    assert model is not None
    assert set(json.keys()) == {
        "id",
        "enabled",
        "families",
        "environment_names",
        "test_case_names",
        "template_ids",
        "test_result_statuses",
        "execution_metadata",
    }
    assert json["id"] == model.id
    assert json["enabled"] == model.enabled
    assert sorted(json["families"]) == sorted(model.families)
    assert sorted(json["environment_names"]) == sorted(model.environment_names)
    assert sorted(json["test_case_names"]) == sorted(model.test_case_names)
    assert sorted(json["template_ids"]) == sorted(model.template_ids)
    assert [s.name for s in sorted(json["test_result_statuses"])] == [
        s.name for s in sorted(model.test_result_statuses)
    ]
    assert sorted(json["execution_metadata"]) == sorted(
        {
            c: [m.value for m in model.execution_metadata if m.category == c]
            for c in {m.category for m in model.execution_metadata}
        }
    )


def test_post_attachment_rule_issue_not_found(
    test_client: TestClient, post_attachment_rule: dict
):
    response = auth_request(
        "post",
        test_client,
        post_endpoint.format(issue_id=999),
        json=post_attachment_rule,
    )

    assert response.status_code == 404


def test_post_attachment_rule(
    test_client: TestClient,
    generator: DataGenerator,
    post_attachment_rule: dict,
    db_session: Session,
):
    issue = generator.gen_issue()

    response = auth_request(
        "post",
        test_client,
        post_endpoint.format(issue_id=issue.id),
        json=post_attachment_rule,
    )

    assert response.status_code == 200
    attachment_rule = db_session.get(
        IssueTestResultAttachmentRule, response.json()["id"]
    )
    _assert_attachment_rule_response(response.json(), attachment_rule)

    issue_response = make_authenticated_request(
        lambda: test_client.get(issue_endpoint.format(issue_id=issue.id)),
        Permission.view_issue,
    )

    assert issue_response.status_code == 200
    assert len(issue_response.json()["attachment_rules"]) == 1
    _assert_attachment_rule_response(
        issue_response.json()["attachment_rules"][0], attachment_rule
    )


def test_post_attachment_rule_twice(
    test_client: TestClient, generator: DataGenerator, post_attachment_rule: dict
):
    issue = generator.gen_issue()

    response_1 = auth_request(
        "post",
        test_client,
        post_endpoint.format(issue_id=issue.id),
        json=post_attachment_rule,
    )
    response_2 = auth_request(
        "post",
        test_client,
        post_endpoint.format(issue_id=issue.id),
        json=post_attachment_rule,
    )

    issue_response = make_authenticated_request(
        lambda: test_client.get(issue_endpoint.format(issue_id=issue.id)),
        Permission.view_issue,
    )

    assert issue_response.status_code == 200
    assert {rule["id"] for rule in issue_response.json()["attachment_rules"]} == {
        response_1.json()["id"],
        response_2.json()["id"],
    }


def test_patch_attachment_rule_no_change(
    test_client: TestClient, generator: DataGenerator, post_attachment_rule: dict
):
    issue = generator.gen_issue()

    post_response = auth_request(
        "post",
        test_client,
        post_endpoint.format(issue_id=issue.id),
        json=post_attachment_rule,
    )
    attachment_rule_id = post_response.json()["id"]

    patch_response = auth_request(
        "patch",
        test_client,
        patch_endpoint.format(issue_id=issue.id, attachment_rule_id=attachment_rule_id),
        json={},
    )

    assert patch_response.status_code == 200
    assert patch_response.json()["enabled"]


def test_patch_attachment_rule_not_found(
    test_client: TestClient, generator: DataGenerator
):
    issue = generator.gen_issue()

    response = auth_request(
        "patch",
        test_client,
        patch_endpoint.format(issue_id=issue.id, attachment_rule_id=999),
        json={},
    )

    assert response.status_code == 404


def test_patch_attachment_rule_wrong_issue(
    test_client: TestClient, generator: DataGenerator, post_attachment_rule: dict
):
    issue = generator.gen_issue()

    post_response = auth_request(
        "post",
        test_client,
        post_endpoint.format(issue_id=issue.id),
        json=post_attachment_rule,
    )
    attachment_rule_id = post_response.json()["id"]

    patch_response = auth_request(
        "patch",
        test_client,
        patch_endpoint.format(
            issue_id=issue.id + 1, attachment_rule_id=attachment_rule_id
        ),
        json={},
    )

    assert patch_response.status_code == 400


def test_patch_attachment_rule_disable(
    test_client: TestClient, generator: DataGenerator, post_attachment_rule: dict
):
    issue = generator.gen_issue()

    post_response = auth_request(
        "post",
        test_client,
        post_endpoint.format(issue_id=issue.id),
        json=post_attachment_rule,
    )
    attachment_rule_id = post_response.json()["id"]

    patch_response = auth_request(
        "patch",
        test_client,
        patch_endpoint.format(issue_id=issue.id, attachment_rule_id=attachment_rule_id),
        json={"enabled": False},
    )

    assert patch_response.status_code == 200
    assert not patch_response.json()["enabled"]


def test_delete_attachment_rule_not_exist(test_client: TestClient):
    response = auth_request(
        "delete",
        test_client,
        delete_endpoint.format(issue_id=999, attachment_rule_id=999),
    )

    assert response.status_code == 204


def test_delete_attachment_rule_wrong_issue(
    test_client: TestClient, generator: DataGenerator, post_attachment_rule: dict
):
    issue = generator.gen_issue()

    post_response = auth_request(
        "post",
        test_client,
        post_endpoint.format(issue_id=issue.id),
        json=post_attachment_rule,
    )
    attachment_rule_id = post_response.json()["id"]

    delete_response = auth_request(
        "delete",
        test_client,
        delete_endpoint.format(
            issue_id=issue.id + 1, attachment_rule_id=attachment_rule_id
        ),
    )

    assert delete_response.status_code == 400


def test_delete_attachment_rule(
    test_client: TestClient,
    generator: DataGenerator,
    post_attachment_rule: dict,
    db_session: Session,
):
    issue = generator.gen_issue()

    post_response = auth_request(
        "post",
        test_client,
        post_endpoint.format(issue_id=issue.id),
        json=post_attachment_rule,
    )
    attachment_rule_id = post_response.json()["id"]

    delete_response = auth_request(
        "delete",
        test_client,
        delete_endpoint.format(
            issue_id=issue.id, attachment_rule_id=attachment_rule_id
        ),
    )

    assert delete_response.status_code == 204

    assert db_session.query(IssueTestResultAttachmentRuleExecutionMetadata).count() == 0


def test_post_attachment_rule_with_test_result_statuses(
    test_client: TestClient, generator: DataGenerator, db_session: Session
):
    """Test creating an attachment rule with test_result_statuses filter."""
    issue = generator.gen_issue()

    response = auth_request(
        "post",
        test_client,
        post_endpoint.format(issue_id=issue.id),
        json={
            "enabled": True,
            "families": ["snap"],
            "environment_names": ["environment-1"],
            "test_case_names": ["test-case-1"],
            "template_ids": ["template-id-1"],
            "test_result_statuses": ["FAILED", "SKIPPED"],
            "execution_metadata": {"category-1": ["value-1"]},
        },
    )

    assert response.status_code == 200
    attachment_rule = db_session.get(
        IssueTestResultAttachmentRule, response.json()["id"]
    )
    assert attachment_rule is not None
    assert len(attachment_rule.test_result_statuses) == 2
    assert {s.name for s in attachment_rule.test_result_statuses} == {
        "FAILED",
        "SKIPPED",
    }


def test_attachment_rule_matches_only_selected_statuses(
    test_client: TestClient,
    test_execution: TestExecution,
    generator: DataGenerator,
    db_session: Session,
):
    """Test that attachment rules filter test results by test_result_statuses."""
    issue = generator.gen_issue()
    test_case = generator.gen_test_case(template_id="template")

    # Create attachment rule that only matches FAILED test results
    rule_response = auth_request(
        "post",
        test_client,
        post_endpoint.format(issue_id=issue.id),
        json={
            "enabled": True,
            "families": [test_execution.artefact_build.artefact.family],
            "environment_names": [test_execution.environment.name],
            "test_case_names": [test_case.name],
            "template_ids": ["template"],
            "test_result_statuses": ["FAILED"],
            "execution_metadata": {},
        },
    )
    assert rule_response.status_code == 200

    # Create test results with different statuses using the data generator
    tr_failed = generator.gen_test_result(
        test_case, test_execution, status=TestResultStatus.FAILED
    )
    apply_test_result_attachment_rules(db_session, tr_failed)
    tr_skipped = generator.gen_test_result(
        test_case, test_execution, status=TestResultStatus.SKIPPED
    )
    apply_test_result_attachment_rules(db_session, tr_skipped)
    tr_passed = generator.gen_test_result(
        test_case, test_execution, status=TestResultStatus.PASSED
    )
    apply_test_result_attachment_rules(db_session, tr_passed)
    db_session.commit()

    # Fetch test results
    response = make_authenticated_request(
        lambda: test_client.get(
            f"/v1/test-executions/{test_execution.id}/test-results"
        ),
        Permission.view_test,
    )

    assert response.status_code == 200
    results = response.json()

    # Only the FAILED result should have the attachment rule applied
    failed_result = next((r for r in results if r["status"] == "FAILED"), None)
    passed_result = next((r for r in results if r["status"] == "PASSED"), None)
    skipped_result = next((r for r in results if r["status"] == "SKIPPED"), None)

    assert failed_result is not None
    assert passed_result is not None
    assert skipped_result is not None

    # FAILED result should have the issue attached via the rule
    assert len(failed_result["issues"]) == 1
    assert failed_result["issues"][0]["issue"]["id"] == issue.id

    # PASSED and SKIPPED results should not have the issue attached
    assert len(passed_result["issues"]) == 0
    assert len(skipped_result["issues"]) == 0


def test_attachment_rule_with_empty_statuses_matches_all(
    test_client: TestClient,
    test_execution: TestExecution,
    generator: DataGenerator,
    db_session: Session,
):
    """Test that attachment rules with empty test_result_statuses match all statuses."""
    issue = generator.gen_issue()
    test_case = generator.gen_test_case(template_id="template")

    # Create attachment rule with no status filter (empty array)
    rule_response = auth_request(
        "post",
        test_client,
        post_endpoint.format(issue_id=issue.id),
        json={
            "enabled": True,
            "families": [test_execution.artefact_build.artefact.family],
            "environment_names": [test_execution.environment.name],
            "test_case_names": [test_case.name],
            "template_ids": ["template"],
            "test_result_statuses": [],
            "execution_metadata": {},
        },
    )
    assert rule_response.status_code == 200

    # Create test results with different statuses using the data generator
    tr_failed = generator.gen_test_result(
        test_case, test_execution, status=TestResultStatus.FAILED
    )
    apply_test_result_attachment_rules(db_session, tr_failed)
    tr_passed = generator.gen_test_result(
        test_case, test_execution, status=TestResultStatus.PASSED
    )
    apply_test_result_attachment_rules(db_session, tr_passed)
    tr_skipped = generator.gen_test_result(
        test_case, test_execution, status=TestResultStatus.SKIPPED
    )
    apply_test_result_attachment_rules(db_session, tr_skipped)
    db_session.commit()

    # Fetch test results
    response = make_authenticated_request(
        lambda: test_client.get(
            f"/v1/test-executions/{test_execution.id}/test-results"
        ),
        Permission.view_test,
    )

    assert response.status_code == 200
    results = response.json()

    # All results should have the issue attached
    for result in results:
        assert len(result["issues"]) == 1
        assert result["issues"][0]["issue"]["id"] == issue.id
