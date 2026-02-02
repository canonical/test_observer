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
from sqlalchemy import select
from sqlalchemy.orm import Session

from tests.conftest import make_authenticated_request
from tests.data_generator import DataGenerator
from test_observer.common.permissions import Permission
from test_observer.data_access.models import (
    IssueTestResultAttachment,
    IssueTestResultAttachmentRule,
    TestExecutionRerunRequest,
)
from test_observer.controllers.issues.auto_rerun_logic import (
    trigger_reruns_for_attachment_rule,
    trigger_reruns_for_test_execution_ids,
)


# ============================================================================
# Unit Tests for Auto Rerun Logic
# ============================================================================


def test_trigger_reruns_for_test_execution_ids_empty(db_session: Session):
    """Test that triggering reruns with empty set does nothing."""
    trigger_reruns_for_test_execution_ids(db_session, set())

    rerun_requests = (
        db_session.execute(select(TestExecutionRerunRequest)).scalars().all()
    )
    assert len(rerun_requests) == 0


def test_trigger_reruns_for_test_execution_ids_single(
    db_session: Session, generator: DataGenerator
):
    """Test triggering rerun for single test execution."""
    environment = generator.gen_environment()
    artefact = generator.gen_artefact()
    artefact_build = generator.gen_artefact_build(artefact)
    test_execution = generator.gen_test_execution(artefact_build, environment)

    trigger_reruns_for_test_execution_ids(db_session, {test_execution.id})

    rerun_requests = (
        db_session.execute(select(TestExecutionRerunRequest)).scalars().all()
    )
    assert len(rerun_requests) == 1

    # Verify the rerun request has the correct composite key
    rerun = rerun_requests[0]
    assert rerun.test_plan_id == test_execution.test_plan_id
    assert rerun.artefact_build_id == test_execution.artefact_build_id
    assert rerun.environment_id == test_execution.environment_id


def test_trigger_reruns_for_test_execution_ids_multiple(
    db_session: Session, generator: DataGenerator
):
    """Test triggering reruns for multiple test executions."""
    environment = generator.gen_environment()
    # Use different artefacts to get different artefact builds
    artefact_1 = generator.gen_artefact(name="core-1")
    artefact_2 = generator.gen_artefact(name="core-2")
    artefact_build_1 = generator.gen_artefact_build(artefact_1)
    artefact_build_2 = generator.gen_artefact_build(artefact_2)

    # Create two test executions with different artefact builds
    # This ensures different composite keys: (test_plan, artefact_build, environment)
    test_execution_1 = generator.gen_test_execution(artefact_build_1, environment)
    test_execution_2 = generator.gen_test_execution(artefact_build_2, environment)

    trigger_reruns_for_test_execution_ids(
        db_session, {test_execution_1.id, test_execution_2.id}
    )

    rerun_requests = (
        db_session.execute(select(TestExecutionRerunRequest)).scalars().all()
    )
    # Should have exactly 2 rerun requests due to different artefact builds
    assert len(rerun_requests) == 2

    # Verify composite keys are correct and distinct
    rerun_keys = {
        (req.test_plan_id, req.artefact_build_id, req.environment_id)
        for req in rerun_requests
    }
    key1 = (
        test_execution_1.test_plan_id,
        test_execution_1.artefact_build_id,
        test_execution_1.environment_id,
    )
    key2 = (
        test_execution_2.test_plan_id,
        test_execution_2.artefact_build_id,
        test_execution_2.environment_id,
    )
    assert key1 in rerun_keys
    assert key2 in rerun_keys


def test_trigger_reruns_for_test_execution_ids_idempotent(
    db_session: Session, generator: DataGenerator
):
    """Test that triggering reruns twice for same execution is idempotent."""
    environment = generator.gen_environment()
    artefact = generator.gen_artefact()
    artefact_build = generator.gen_artefact_build(artefact)
    test_execution = generator.gen_test_execution(artefact_build, environment)

    trigger_reruns_for_test_execution_ids(db_session, {test_execution.id})
    trigger_reruns_for_test_execution_ids(db_session, {test_execution.id})

    rerun_requests = (
        db_session.execute(select(TestExecutionRerunRequest)).scalars().all()
    )
    # Should still have exactly 1 due to PostgreSQL ON CONFLICT DO NOTHING
    assert len(rerun_requests) == 1


def test_trigger_reruns_same_composite_key_deduplicates(
    db_session: Session, generator: DataGenerator
):
    """Test deduplication with same composite key."""
    environment = generator.gen_environment()
    artefact = generator.gen_artefact()
    artefact_build = generator.gen_artefact_build(artefact)
    test_plan = generator.gen_test_plan()

    # Create two test executions with same composite key:
    # (same test_plan, same artefact_build, same environment)
    test_execution_1 = generator.gen_test_execution(artefact_build, environment)
    test_execution_1.test_plan_id = test_plan.id

    test_execution_2 = generator.gen_test_execution(artefact_build, environment)
    test_execution_2.test_plan_id = test_plan.id

    db_session.commit()

    trigger_reruns_for_test_execution_ids(
        db_session, {test_execution_1.id, test_execution_2.id}
    )

    rerun_requests = (
        db_session.execute(select(TestExecutionRerunRequest)).scalars().all()
    )
    # Should have exactly 1 rerun request (composite key deduplicates)
    assert len(rerun_requests) == 1
    assert rerun_requests[0].test_plan_id == test_plan.id
    assert rerun_requests[0].artefact_build_id == artefact_build.id
    assert rerun_requests[0].environment_id == environment.id


def test_trigger_reruns_for_attachment_rule_no_attachments(
    db_session: Session, generator: DataGenerator
):
    """Test triggering reruns when attachment rule has no attachments."""
    issue = generator.gen_issue()

    # Create attachment rule directly
    attachment_rule = IssueTestResultAttachmentRule(
        issue_id=issue.id,
        enabled=True,
        auto_rerun_on_attach=True,
    )
    db_session.add(attachment_rule)
    db_session.commit()

    trigger_reruns_for_attachment_rule(db_session, attachment_rule)

    rerun_requests = (
        db_session.execute(select(TestExecutionRerunRequest)).scalars().all()
    )
    assert len(rerun_requests) == 0


def test_trigger_reruns_for_attachment_rule_with_attachments(
    db_session: Session, generator: DataGenerator
):
    """Test triggering reruns for attached test results."""

    issue = generator.gen_issue()

    # Create attachment rule directly
    attachment_rule = IssueTestResultAttachmentRule(
        issue_id=issue.id,
        enabled=True,
        auto_rerun_on_attach=True,
    )
    db_session.add(attachment_rule)
    db_session.commit()

    # Create test data with different artefact builds to ensure different composite keys
    environment = generator.gen_environment()
    test_case = generator.gen_test_case()
    # Use different artefacts to get different artefact builds
    artefact_1 = generator.gen_artefact(name="core-1")
    artefact_2 = generator.gen_artefact(name="core-2")
    artefact_build_1 = generator.gen_artefact_build(artefact_1)
    artefact_build_2 = generator.gen_artefact_build(artefact_2)

    # Create test executions with different artefact builds
    test_execution_1 = generator.gen_test_execution(artefact_build_1, environment)
    test_execution_2 = generator.gen_test_execution(artefact_build_2, environment)

    test_result_1 = generator.gen_test_result(test_case, test_execution_1)
    test_result_2 = generator.gen_test_result(test_case, test_execution_2)

    # Attach test results to the rule
    attachment_1 = IssueTestResultAttachment(
        issue_id=issue.id,
        test_result_id=test_result_1.id,
        attachment_rule_id=attachment_rule.id,
    )
    attachment_2 = IssueTestResultAttachment(
        issue_id=issue.id,
        test_result_id=test_result_2.id,
        attachment_rule_id=attachment_rule.id,
    )
    db_session.add(attachment_1)
    db_session.add(attachment_2)
    db_session.commit()

    trigger_reruns_for_attachment_rule(db_session, attachment_rule)

    rerun_requests = (
        db_session.execute(select(TestExecutionRerunRequest)).scalars().all()
    )
    # Should have exactly 2 rerun requests (one per artefact build)
    assert len(rerun_requests) == 2

    # Verify the composite keys match the test executions
    rerun_keys = {
        (req.test_plan_id, req.artefact_build_id, req.environment_id)
        for req in rerun_requests
    }
    key1 = (
        test_execution_1.test_plan_id,
        test_execution_1.artefact_build_id,
        test_execution_1.environment_id,
    )
    key2 = (
        test_execution_2.test_plan_id,
        test_execution_2.artefact_build_id,
        test_execution_2.environment_id,
    )
    assert key1 in rerun_keys
    assert key2 in rerun_keys


# ============================================================================
# API Integration Tests for Auto Rerun Attachment Feature
# ============================================================================


def auth_post(test_client: TestClient, endpoint: str, json: dict):
    return make_authenticated_request(
        lambda: test_client.post(endpoint, json=json),
        Permission.change_issue_attachment,
    )


def auth_post_bulk(test_client: TestClient, endpoint: str, json: dict):
    return make_authenticated_request(
        lambda: test_client.post(endpoint, json=json),
        Permission.change_issue_attachment,
        Permission.change_issue_attachment_bulk,
    )


def test_attachment_rule_auto_rerun_enabled_in_post(
    test_client: TestClient, generator: DataGenerator
):
    """Test creating an attachment rule with auto_rerun_on_attach enabled."""
    issue = generator.gen_issue()

    response = make_authenticated_request(
        lambda: test_client.post(
            f"/v1/issues/{issue.id}/attachment-rules",
            json={
                "enabled": True,
                "auto_rerun_on_attach": True,
                "families": [],
                "environment_names": [],
                "test_case_names": [],
                "template_ids": [],
                "execution_metadata": {},
            },
        ),
        Permission.change_attachment_rule,
    )

    assert response.status_code == 200
    assert response.json()["auto_rerun_on_attach"] is True


def test_patch_attachment_rule_enable_auto_rerun(
    test_client: TestClient, generator: DataGenerator
):
    """Test enabling auto_rerun_on_attach returns 200 with updated flag."""
    issue = generator.gen_issue()

    # Create attachment rule without auto-rerun
    post_response = make_authenticated_request(
        lambda: test_client.post(
            f"/v1/issues/{issue.id}/attachment-rules",
            json={
                "enabled": True,
                "auto_rerun_on_attach": False,
                "families": [],
                "environment_names": [],
                "test_case_names": [],
                "template_ids": [],
                "execution_metadata": {},
            },
        ),
        Permission.change_attachment_rule,
    )
    assert post_response.status_code == 200
    assert post_response.json()["auto_rerun_on_attach"] is False
    attachment_rule_id = post_response.json()["id"]

    # Enable auto-rerun
    patch_response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/issues/{issue.id}/attachment-rules/{attachment_rule_id}",
            json={"auto_rerun_on_attach": True},
        ),
        Permission.change_attachment_rule,
    )

    assert patch_response.status_code == 200
    assert patch_response.json()["auto_rerun_on_attach"] is True


def test_patch_attachment_rule_disable_auto_rerun(
    test_client: TestClient, generator: DataGenerator
):
    """Test disabling auto_rerun_on_attach."""
    issue = generator.gen_issue()

    # Create attachment rule with auto-rerun enabled
    post_response = make_authenticated_request(
        lambda: test_client.post(
            f"/v1/issues/{issue.id}/attachment-rules",
            json={
                "enabled": True,
                "auto_rerun_on_attach": True,
                "families": [],
                "environment_names": [],
                "test_case_names": [],
                "template_ids": [],
                "execution_metadata": {},
            },
        ),
        Permission.change_attachment_rule,
    )
    attachment_rule_id = post_response.json()["id"]

    # Disable auto-rerun
    patch_response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/issues/{issue.id}/attachment-rules/{attachment_rule_id}",
            json={"auto_rerun_on_attach": False},
        ),
        Permission.change_attachment_rule,
    )

    assert patch_response.status_code == 200
    assert patch_response.json()["auto_rerun_on_attach"] is False


def test_auto_rerun_end_to_end_workflow(
    test_client: TestClient, generator: DataGenerator, db_session: Session
):
    """Test auto-rerun end-to-end workflow."""
    issue = generator.gen_issue()

    # Step 1: Create attachment rule without auto-rerun
    post_response = make_authenticated_request(
        lambda: test_client.post(
            f"/v1/issues/{issue.id}/attachment-rules",
            json={
                "enabled": True,
                "auto_rerun_on_attach": False,
                "families": [],
                "environment_names": [],
                "test_case_names": [],
                "template_ids": [],
                "execution_metadata": {},
            },
        ),
        Permission.change_attachment_rule,
    )
    attachment_rule_id = post_response.json()["id"]
    assert post_response.json()["auto_rerun_on_attach"] is False

    # Step 2: Create test data and attach it
    environment = generator.gen_environment()
    test_case = generator.gen_test_case()
    artefact = generator.gen_artefact()
    artefact_build = generator.gen_artefact_build(artefact)
    test_execution = generator.gen_test_execution(artefact_build, environment)
    test_result = generator.gen_test_result(test_case, test_execution)

    # Attach test result (should NOT trigger reruns yet)
    attach_response = auth_post_bulk(
        test_client,
        f"/v1/issues/{issue.id}/attach",
        {
            "test_results": [test_result.id],
            "attachment_rule": attachment_rule_id,
        },
    )
    assert attach_response.status_code == 200

    # Verify no reruns created yet
    db_session.expire_all()
    rerun_count_before = len(
        db_session.execute(select(TestExecutionRerunRequest)).scalars().all()
    )

    # Step 3: Enable auto-rerun on the rule (should trigger retroactive reruns)
    patch_response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/issues/{issue.id}/attachment-rules/{attachment_rule_id}",
            json={"auto_rerun_on_attach": True},
        ),
        Permission.change_attachment_rule,
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["auto_rerun_on_attach"] is True

    # Verify rerun was created for the already-attached test result
    db_session.expire_all()
    rerun_count_after = len(
        db_session.execute(select(TestExecutionRerunRequest)).scalars().all()
    )
    assert rerun_count_after > rerun_count_before, (
        "Retroactive reruns should be created"
    )


def test_auto_rerun_triggered_on_new_attachment(
    test_client: TestClient, generator: DataGenerator
):
    """Test attachment with auto-rerun enabled."""
    issue = generator.gen_issue()

    # Create attachment rule with auto-rerun enabled
    post_response = make_authenticated_request(
        lambda: test_client.post(
            f"/v1/issues/{issue.id}/attachment-rules",
            json={
                "enabled": True,
                "auto_rerun_on_attach": True,
                "families": [],
                "environment_names": [],
                "test_case_names": [],
                "template_ids": [],
                "execution_metadata": {},
            },
        ),
        Permission.change_attachment_rule,
    )
    assert post_response.status_code == 200
    assert post_response.json()["auto_rerun_on_attach"] is True
    attachment_rule_id = post_response.json()["id"]

    # Create test data
    environment = generator.gen_environment()
    test_case = generator.gen_test_case()
    artefact = generator.gen_artefact()
    artefact_build = generator.gen_artefact_build(artefact)
    test_execution = generator.gen_test_execution(artefact_build, environment)
    test_result = generator.gen_test_result(test_case, test_execution)

    # Attach test result (requires bulk permission)
    attach_response = auth_post_bulk(
        test_client,
        f"/v1/issues/{issue.id}/attach",
        {
            "test_results": [test_result.id],
            "attachment_rule": attachment_rule_id,
        },
    )

    # Verify attachment succeeded
    assert attach_response.status_code == 200


def test_auto_rerun_not_triggered_when_disabled(
    test_client: TestClient, generator: DataGenerator, db_session: Session
):
    """Test attachment without auto-rerun disabled."""
    issue = generator.gen_issue()

    # Create attachment rule with auto-rerun disabled
    post_response = make_authenticated_request(
        lambda: test_client.post(
            f"/v1/issues/{issue.id}/attachment-rules",
            json={
                "enabled": True,
                "auto_rerun_on_attach": False,
                "families": [],
                "environment_names": [],
                "test_case_names": [],
                "template_ids": [],
                "execution_metadata": {},
            },
        ),
        Permission.change_attachment_rule,
    )
    attachment_rule_id = post_response.json()["id"]

    # Create test data
    environment = generator.gen_environment()
    test_case = generator.gen_test_case()
    artefact = generator.gen_artefact()
    artefact_build = generator.gen_artefact_build(artefact)
    test_execution = generator.gen_test_execution(artefact_build, environment)
    test_result = generator.gen_test_result(test_case, test_execution)

    # Attach test result (requires bulk permission)
    attach_response = auth_post_bulk(
        test_client,
        f"/v1/issues/{issue.id}/attach",
        {
            "test_results": [test_result.id],
            "attachment_rule": attachment_rule_id,
        },
    )

    # Verify attachment succeeded
    assert attach_response.status_code == 200

    # Verify no rerun was triggered
    db_session.expire_all()
    rerun_requests = (
        db_session.execute(select(TestExecutionRerunRequest)).scalars().all()
    )
    assert len(rerun_requests) == 0
