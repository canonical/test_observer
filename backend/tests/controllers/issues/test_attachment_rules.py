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
        "execution_metadata",
    }
    assert json["id"] == model.id
    assert json["enabled"] == model.enabled
    assert sorted(json["families"]) == sorted(model.families)
    assert sorted(json["environment_names"]) == sorted(model.environment_names)
    assert sorted(json["test_case_names"]) == sorted(model.test_case_names)
    assert sorted(json["template_ids"]) == sorted(model.template_ids)
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

    issue_response = test_client.get(issue_endpoint.format(issue_id=issue.id))

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

    issue_response = test_client.get(issue_endpoint.format(issue_id=issue.id))

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
