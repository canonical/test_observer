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

from tests.data_generator import DataGenerator
from sqlalchemy.orm import Session
from test_observer.data_access.models import (
    IssueTestResultAttachmentRuleExecutionMetadata,
)

issue_endpoint = "/v1/issues/{issue_id}"
post_endpoint = issue_endpoint + "/attachment-rules"
patch_endpoint = post_endpoint + "/{attachment_rule_id}"
delete_endpoint = patch_endpoint


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


def test_post_attachment_rule_issue_not_found(
    test_client: TestClient, post_attachment_rule: dict
):
    response = test_client.post(
        post_endpoint.format(issue_id=999), json=post_attachment_rule
    )

    assert response.status_code == 404


def test_post_attachment_rule(
    test_client: TestClient, generator: DataGenerator, post_attachment_rule: dict
):
    issue = generator.gen_issue()

    response = test_client.post(
        post_endpoint.format(issue_id=issue.id), json=post_attachment_rule
    )

    assert response.status_code == 200
    assert set(response.json().keys()) == {
        "environment_names",
        "execution_metadata",
        "id",
        "families",
        "template_ids",
        "enabled",
        "test_case_names",
    }
    assert response.json()["enabled"]
    assert response.json()["families"] == ["charm"]
    assert response.json()["environment_names"] == ["environment-1"]
    assert response.json()["test_case_names"] == ["test-case-1"]
    assert response.json()["template_ids"] == ["template-id-1"]
    assert response.json()["execution_metadata"] == {
        "category-1": ["value-1", "value-2"]
    }

    issue_response = test_client.get(issue_endpoint.format(issue_id=issue.id))

    assert issue_response.status_code == 200
    assert len(issue_response.json()["attachment_rules"]) == 1
    assert issue_response.json()["attachment_rules"][0]["id"] == response.json()["id"]


def test_post_attachment_rule_twice(
    test_client: TestClient, generator: DataGenerator, post_attachment_rule: dict
):
    issue = generator.gen_issue()

    response_1 = test_client.post(
        post_endpoint.format(issue_id=issue.id), json=post_attachment_rule
    )

    response_2 = test_client.post(
        post_endpoint.format(issue_id=issue.id), json=post_attachment_rule
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

    post_response = test_client.post(
        post_endpoint.format(issue_id=issue.id), json=post_attachment_rule
    )
    attachment_rule_id = post_response.json()["id"]

    patch_response = test_client.patch(
        patch_endpoint.format(issue_id=issue.id, attachment_rule_id=attachment_rule_id),
        json={},
    )

    assert patch_response.status_code == 200
    assert patch_response.json()["enabled"]


def test_patch_attachment_rule_not_found(
    test_client: TestClient, generator: DataGenerator
):
    issue = generator.gen_issue()

    response = test_client.patch(
        patch_endpoint.format(issue_id=issue.id, attachment_rule_id=999),
        json={},
    )

    assert response.status_code == 404


def test_patch_attachment_rule_wrong_issue(
    test_client: TestClient, generator: DataGenerator, post_attachment_rule: dict
):
    issue = generator.gen_issue()

    post_response = test_client.post(
        post_endpoint.format(issue_id=issue.id), json=post_attachment_rule
    )
    attachment_rule_id = post_response.json()["id"]

    patch_response = test_client.patch(
        patch_endpoint.format(
            issue_id=issue.id + 1, attachment_rule_id=attachment_rule_id
        ),
        json={},
    )

    assert patch_response.status_code == 403


def test_patch_attachment_rule_disable(
    test_client: TestClient, generator: DataGenerator, post_attachment_rule: dict
):
    issue = generator.gen_issue()

    post_response = test_client.post(
        post_endpoint.format(issue_id=issue.id), json=post_attachment_rule
    )
    attachment_rule_id = post_response.json()["id"]

    patch_response = test_client.patch(
        patch_endpoint.format(issue_id=issue.id, attachment_rule_id=attachment_rule_id),
        json={"enabled": False},
    )

    assert patch_response.status_code == 200
    assert not patch_response.json()["enabled"]


def test_delete_attachment_rule_not_exist(test_client: TestClient):
    response = test_client.delete(
        delete_endpoint.format(issue_id=999, attachment_rule_id=999),
    )

    assert response.status_code == 204


def test_delete_attachment_rule_wrong_issue(
    test_client: TestClient, generator: DataGenerator, post_attachment_rule: dict
):
    issue = generator.gen_issue()

    post_response = test_client.post(
        post_endpoint.format(issue_id=issue.id), json=post_attachment_rule
    )
    attachment_rule_id = post_response.json()["id"]

    delete_response = test_client.delete(
        delete_endpoint.format(
            issue_id=issue.id + 1, attachment_rule_id=attachment_rule_id
        )
    )

    assert delete_response.status_code == 403


def test_delete_attachment_rule(
    test_client: TestClient,
    generator: DataGenerator,
    post_attachment_rule: dict,
    db_session: Session,
):
    issue = generator.gen_issue()

    post_response = test_client.post(
        post_endpoint.format(issue_id=issue.id), json=post_attachment_rule
    )
    attachment_rule_id = post_response.json()["id"]

    delete_response = test_client.delete(
        delete_endpoint.format(issue_id=issue.id, attachment_rule_id=attachment_rule_id)
    )

    assert delete_response.status_code == 204

    assert db_session.query(IssueTestResultAttachmentRuleExecutionMetadata).count() == 0
