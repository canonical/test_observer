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
from sqlalchemy.orm import Session

from tests.conftest import make_authenticated_request
from tests.data_generator import DataGenerator
from test_observer.common.permissions import Permission
from test_observer.data_access.models import (
    IssueTestResultAttachmentRule,
    TestExecutionRerunRequest,
)
from test_observer.data_access.models_enums import FamilyName
from test_observer.controllers.issues.attachment_rules_logic import (
    apply_test_result_attachment_rules,
)


def test_issue_auto_rerun_enabled_default_false(
    test_client: TestClient,
    generator: DataGenerator,
):
    """Test that new issues have auto_rerun_enabled set to False by default"""
    issue = generator.gen_issue()

    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/issues/{issue.id}"),
        Permission.view_issue,
    )

    assert response.status_code == 200
    assert response.json()["auto_rerun_enabled"] is False


def test_patch_issue_auto_rerun_endpoint(
    test_client: TestClient,
    generator: DataGenerator,
):
    """Test PATCH /v1/issues/{issue_id} endpoint"""
    issue = generator.gen_issue()

    # Enable auto-rerun
    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/issues/{issue.id}",
            json={"auto_rerun_enabled": True},
        ),
        Permission.change_auto_rerun,
    )

    assert response.status_code == 200
    assert response.json()["auto_rerun_enabled"] is True

    # Disable auto-rerun
    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/issues/{issue.id}",
            json={"auto_rerun_enabled": False},
        ),
        Permission.change_auto_rerun,
    )

    assert response.status_code == 200
    assert response.json()["auto_rerun_enabled"] is False


def test_patch_issue_auto_rerun_requires_permission(
    test_client: TestClient,
    generator: DataGenerator,
):
    """Test that change_auto_rerun permission is required"""
    issue = generator.gen_issue()

    # Try without permission
    response = test_client.patch(
        f"/v1/issues/{issue.id}",
        json={"auto_rerun_enabled": True},
    )

    assert response.status_code == 403


def test_patch_issue_auto_rerun_not_found(
    test_client: TestClient,
):
    """Test PATCH auto-rerun with non-existent issue returns 404"""
    response = make_authenticated_request(
        lambda: test_client.patch(
            "/v1/issues/999999",
            json={"auto_rerun_enabled": True},
        ),
        Permission.change_auto_rerun,
    )

    assert response.status_code == 404


def test_auto_rerun_creates_rerun_request_when_enabled(
    generator: DataGenerator,
    db_session: Session,
):
    """Test that matching test results trigger rerun requests when auto_rerun is enabled"""
    # Create test data
    artefact = generator.gen_artefact(family=FamilyName.snap)
    artefact_build = generator.gen_artefact_build(artefact=artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build=artefact_build, environment=environment
    )
    test_case = generator.gen_test_case()
    test_result = generator.gen_test_result(
        test_case=test_case, test_execution=test_execution
    )
    
    # Create issue with auto_rerun enabled
    issue = generator.gen_issue()
    issue.auto_rerun_enabled = True
    db_session.commit()

    # Create attachment rule that matches
    attachment_rule = IssueTestResultAttachmentRule(
        issue=issue,
        families=[FamilyName.snap],
    )
    db_session.add(attachment_rule)
    db_session.commit()

    # Verify no rerun requests exist yet
    rerun_requests_before = db_session.query(TestExecutionRerunRequest).count()
    assert rerun_requests_before == 0

    # Apply attachment rules
    apply_test_result_attachment_rules(db_session, test_result)

    # Verify rerun request was created
    rerun_requests = db_session.query(TestExecutionRerunRequest).all()
    assert len(rerun_requests) == 1
    assert rerun_requests[0].test_plan_id == test_execution.test_plan_id
    assert rerun_requests[0].artefact_build_id == test_execution.artefact_build_id
    assert rerun_requests[0].environment_id == test_execution.environment_id


def test_auto_rerun_does_not_create_rerun_request_when_disabled(
    generator: DataGenerator,
    db_session: Session,
):
    """Test that rerun requests are NOT created when auto_rerun is disabled"""
    # Create test data
    artefact = generator.gen_artefact(family=FamilyName.snap)
    artefact_build = generator.gen_artefact_build(artefact=artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build=artefact_build, environment=environment
    )
    test_case = generator.gen_test_case()
    test_result = generator.gen_test_result(
        test_case=test_case, test_execution=test_execution
    )
    
    # Create issue with auto_rerun DISABLED (default)
    issue = generator.gen_issue()
    assert issue.auto_rerun_enabled is False

    # Create attachment rule that matches
    attachment_rule = IssueTestResultAttachmentRule(
        issue=issue,
        families=[FamilyName.snap],
    )
    db_session.add(attachment_rule)
    db_session.commit()

    # Apply attachment rules
    apply_test_result_attachment_rules(db_session, test_result)

    # Verify NO rerun request was created
    rerun_requests = db_session.query(TestExecutionRerunRequest).all()
    assert len(rerun_requests) == 0


def test_auto_rerun_multiple_issues_with_different_settings(
    generator: DataGenerator,
    db_session: Session,
):
    """Test that only issues with auto_rerun enabled trigger reruns"""
    # Create test data
    artefact = generator.gen_artefact(family=FamilyName.snap)
    artefact_build = generator.gen_artefact_build(artefact=artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build=artefact_build, environment=environment
    )
    test_case = generator.gen_test_case()
    test_result = generator.gen_test_result(
        test_case=test_case, test_execution=test_execution
    )
    
    # Create issue 1 with auto_rerun enabled
    issue1 = generator.gen_issue(key="1")
    issue1.auto_rerun_enabled = True
    
    # Create issue 2 with auto_rerun disabled
    issue2 = generator.gen_issue(key="2")
    issue2.auto_rerun_enabled = False
    
    db_session.commit()

    # Create attachment rules that match for both issues
    attachment_rule1 = IssueTestResultAttachmentRule(
        issue=issue1,
        families=[FamilyName.snap],
    )
    attachment_rule2 = IssueTestResultAttachmentRule(
        issue=issue2,
        families=[FamilyName.snap],
    )
    db_session.add_all([attachment_rule1, attachment_rule2])
    db_session.commit()

    # Apply attachment rules
    apply_test_result_attachment_rules(db_session, test_result)

    # Verify both issues are attached
    assert len(test_result.issue_attachments) == 2

    # Verify only ONE rerun request was created (for issue1)
    rerun_requests = db_session.query(TestExecutionRerunRequest).all()
    assert len(rerun_requests) == 1


def test_auto_rerun_no_duplicate_rerun_requests(
    generator: DataGenerator,
    db_session: Session,
):
    """Test that duplicate rerun requests are not created"""
    # Create test data
    artefact = generator.gen_artefact(family=FamilyName.snap)
    artefact_build = generator.gen_artefact_build(artefact=artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build=artefact_build, environment=environment
    )
    test_case1 = generator.gen_test_case(name="test1")
    test_case2 = generator.gen_test_case(name="test2")
    test_result1 = generator.gen_test_result(
        test_case=test_case1, test_execution=test_execution
    )
    test_result2 = generator.gen_test_result(
        test_case=test_case2, test_execution=test_execution
    )
    
    # Create issue with auto_rerun enabled
    issue = generator.gen_issue()
    issue.auto_rerun_enabled = True
    db_session.commit()

    # Create attachment rule that matches
    attachment_rule = IssueTestResultAttachmentRule(
        issue=issue,
        families=[FamilyName.snap],
    )
    db_session.add(attachment_rule)
    db_session.commit()

    # Apply attachment rules to first test result
    apply_test_result_attachment_rules(db_session, test_result1)

    # Verify rerun request was created
    rerun_requests = db_session.query(TestExecutionRerunRequest).all()
    assert len(rerun_requests) == 1

    # Apply attachment rules to second test result from same execution
    apply_test_result_attachment_rules(db_session, test_result2)

    # Verify NO duplicate rerun request was created
    rerun_requests = db_session.query(TestExecutionRerunRequest).all()
    assert len(rerun_requests) == 1


def test_patch_issue_auto_rerun_via_general_patch(
    test_client: TestClient,
    generator: DataGenerator,
):
    """Test that auto_rerun can also be patched via general PATCH endpoint"""
    issue = generator.gen_issue()

    # Enable auto-rerun via general patch endpoint
    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/issues/{issue.id}",
            json={"auto_rerun_enabled": True},
        ),
        Permission.change_issue,
    )

    assert response.status_code == 200
    assert response.json()["auto_rerun_enabled"] is True

    # Verify via GET
    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/issues/{issue.id}"),
        Permission.view_issue,
    )
    assert response.json()["auto_rerun_enabled"] is True
