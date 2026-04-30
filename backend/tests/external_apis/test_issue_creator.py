# Copyright 2026 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from unittest.mock import Mock

import pytest

from test_observer.common.helpers import get_artefact_url
from test_observer.data_access.models_enums import FamilyName, NotificationType
from test_observer.external_apis.issue_creator import IssueCreator, JiraIssueContext
from tests.data_generator import DataGenerator


class TestCreateIssue:
    """Test create_issue method"""

    def test_create_issue_with_jira_client(self):
        """Test creating issue with Jira client"""
        mock_jira = Mock()
        jira_ctx = JiraIssueContext(client=mock_jira, parent_issue="TO-123")
        creator = IssueCreator(jira_ctx=jira_ctx)

        creator.create_issue(
            summary="Test Issue",
            description="Test description",
            issue_type="Task",
        )

        mock_jira.create_issue.assert_called_once_with(
            project_key="TO",
            summary="Test Issue",
            issue_type="Task",
            description="Test description",
            parent_issue_key="TO-123",
            assignee_id=None,
        )

    def test_create_issue_forwards_assignee(self):
        """Test that assignee_id is forwarded to Jira client"""
        mock_jira = Mock()
        jira_ctx = JiraIssueContext(client=mock_jira, parent_issue="TO-123")
        creator = IssueCreator(jira_ctx=jira_ctx)

        creator.create_issue(
            summary="Test Issue",
            description="Test description",
            assignee_id="alice-handle",
        )

        mock_jira.create_issue.assert_called_once_with(
            project_key="TO",
            summary="Test Issue",
            issue_type="Task",
            description="Test description",
            parent_issue_key="TO-123",
            assignee_id="alice-handle",
        )


class TestCreateReviewIssue:
    """Test create_review_issue method"""

    def test_create_review_issue_artefact_review(self, generator: DataGenerator):
        """Test successful creation of artefact review issue"""
        mock_jira = Mock()
        mock_jira.get_account_id_by_username.return_value = "jira-account-abc"
        jira_ctx = JiraIssueContext(client=mock_jira, parent_issue="TO-123")
        reviewer = generator.gen_user(name="Alice", email="alice@example.com", launchpad_handle="alice-lp")
        artefact = generator.gen_artefact(
            name="test-snap",
            version="1.0.0",
            reviewers=[reviewer],
        )

        creator = IssueCreator(jira_ctx=jira_ctx)
        creator.create_review_issue(artefact, reviewer, NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW)

        mock_jira.get_account_id_by_username.assert_called_once_with("alice-lp")
        mock_jira.create_issue.assert_called_once()

        expected_artefact_url = get_artefact_url(artefact)
        call = mock_jira.create_issue.call_args_list[0]
        assert call.kwargs["project_key"] == "TO"
        assert call.kwargs["summary"] == "Review artefact test-snap version 1.0.0 - Alice"
        assert (
            call.kwargs["description"]
            == f"Review artefact test-snap version 1.0.0\n\nArtefact page: {expected_artefact_url}"
        )
        assert call.kwargs["issue_type"] == "Task"
        assert call.kwargs["parent_issue_key"] == "TO-123"
        assert call.kwargs["assignee_id"] == "jira-account-abc"

    def test_create_review_issue_environment_review(self, generator: DataGenerator):
        """Test successful creation of environment review issue"""
        mock_jira = Mock()
        mock_jira.get_account_id_by_username.return_value = "jira-account-abc"
        jira_ctx = JiraIssueContext(client=mock_jira, parent_issue="TO-123")
        reviewer = generator.gen_user(name="Alice", email="alice@example.com", launchpad_handle="alice-lp")
        artefact = generator.gen_artefact(
            name="test-snap",
            version="1.0.0",
            reviewers=[reviewer],
        )

        creator = IssueCreator(jira_ctx=jira_ctx)
        creator.create_review_issue(artefact, reviewer, NotificationType.USER_ASSIGNED_ENVIRONMENT_REVIEW)

        mock_jira.get_account_id_by_username.assert_called_once_with("alice-lp")
        mock_jira.create_issue.assert_called_once()

        expected_artefact_url = get_artefact_url(artefact)
        call = mock_jira.create_issue.call_args_list[0]
        assert call.kwargs["project_key"] == "TO"
        assert call.kwargs["summary"] == "Review environments of Artefact test-snap version 1.0.0 - Alice"
        assert call.kwargs["description"] == (
            f"Review test environments for artefact test-snap version 1.0.0\n\nArtefact page: {expected_artefact_url}"
        )
        assert call.kwargs["issue_type"] == "Task"
        assert call.kwargs["parent_issue_key"] == "TO-123"
        assert call.kwargs["assignee_id"] == "jira-account-abc"

    def test_create_review_issue_success(self, generator: DataGenerator):
        """Test successful creation of review issues"""
        mock_jira = Mock()
        mock_jira.get_account_id_by_username.return_value = "jira-account-abc"
        jira_ctx = JiraIssueContext(client=mock_jira, parent_issue="TO-123")
        reviewer = generator.gen_user(name="Alice", email="alice@example.com", launchpad_handle="alice-lp")
        artefact = generator.gen_artefact(
            name="test-snap",
            version="1.0.0",
            reviewers=[reviewer],
        )

        creator = IssueCreator(jira_ctx=jira_ctx)
        creator.create_review_issue(artefact, reviewer, NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW)

        assert mock_jira.get_account_id_by_username.call_count == 1
        mock_jira.get_account_id_by_username.assert_called_with("alice-lp")

        # Should call create_issue once via Jira client
        assert mock_jira.create_issue.call_count == 1

        expected_artefact_url = get_artefact_url(artefact)

        first_call = mock_jira.create_issue.call_args_list[0]
        assert first_call.kwargs["project_key"] == "TO"
        assert first_call.kwargs["summary"] == "Review artefact test-snap version 1.0.0 - Alice"
        assert (
            first_call.kwargs["description"]
            == f"Review artefact test-snap version 1.0.0\n\nArtefact page: {expected_artefact_url}"
        )
        assert first_call.kwargs["issue_type"] == "Task"
        assert first_call.kwargs["parent_issue_key"] == "TO-123"
        assert first_call.kwargs["assignee_id"] == "jira-account-abc"

    def test_create_review_issue_reviewer_not_in_jira(self, generator: DataGenerator):
        """Test that issues are not created when reviewer is not found in Jira"""
        mock_jira = Mock()
        mock_jira.get_account_id_by_username.return_value = None
        jira_ctx = JiraIssueContext(client=mock_jira, parent_issue="TO-123")
        reviewer = generator.gen_user(name="Alice", email="alice@example.com", launchpad_handle="alice-lp")
        artefact = generator.gen_artefact(
            name="test-snap",
            version="1.0.0",
            reviewers=[reviewer],
        )

        creator = IssueCreator(jira_ctx=jira_ctx)
        with pytest.raises(ValueError, match="Cannot assign Jira issue to reviewer"):
            creator.create_review_issue(artefact, reviewer, NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW)

        mock_jira.get_account_id_by_username.assert_called_once_with("alice-lp")
        assert mock_jira.create_issue.call_count == 0

    def test_create_review_issue_reviewer_without_launchpad_handle(self, generator: DataGenerator):
        """Test that issues are not created when reviewer has no launchpad handle"""
        mock_jira = Mock()
        jira_ctx = JiraIssueContext(client=mock_jira, parent_issue="TO-123")
        reviewer = generator.gen_user(name="Alice", email="alice@example.com", launchpad_handle=None)
        artefact = generator.gen_artefact(
            name="test-snap",
            version="1.0.0",
            reviewers=[reviewer],
        )

        creator = IssueCreator(jira_ctx=jira_ctx)

        with pytest.raises(ValueError, match="does not have a launchpad handle"):
            creator.create_review_issue(artefact, reviewer, NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW)

        mock_jira.get_account_id_by_username.assert_not_called()
        assert mock_jira.create_issue.call_count == 0

    def test_create_review_issue_no_reviewers(self, generator: DataGenerator):
        """Test that ValueError is raised when artefact has no reviewers"""
        mock_jira = Mock()
        jira_ctx = JiraIssueContext(client=mock_jira, parent_issue="TO-123")
        reviewer = generator.gen_user(name="Alice", email="alice@example.com")
        artefact = generator.gen_artefact(
            name="test-snap",
            version="1.0.0",
            reviewers=[],
        )

        creator = IssueCreator(jira_ctx=jira_ctx)

        with pytest.raises(ValueError, match="Cannot create review cards for non-reviewer"):
            creator.create_review_issue(artefact, reviewer, NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW)

        mock_jira.create_issue.assert_not_called()

    def test_create_review_issue_invalid_reviewer(self, generator: DataGenerator):
        """Test that ValueError is raised when reviewer is not in artefact's reviewer list"""
        mock_jira = Mock()
        jira_ctx = JiraIssueContext(client=mock_jira, parent_issue="TO-123")
        valid_reviewer = generator.gen_user(name="Alice", email="alice@example.com")
        invalid_reviewer = generator.gen_user(name="Bob", email="bob@example.com")
        artefact = generator.gen_artefact(
            name="test-snap",
            version="1.0.0",
            reviewers=[valid_reviewer],
        )

        creator = IssueCreator(jira_ctx=jira_ctx)

        with pytest.raises(ValueError, match="reviewers do not include user"):
            creator.create_review_issue(artefact, invalid_reviewer, NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW)

        mock_jira.create_issue.assert_not_called()


class TestGetArtefactUrl:
    """Test get_artefact_url helper function"""

    def test_snap_url_generation(self, generator: DataGenerator):
        """Test URL generation for snap artefacts"""
        artefact = generator.gen_artefact(name="test-snap", version="1.0.0")
        # Default family for artefact is snap
        url = get_artefact_url(artefact)
        assert url == f"http://localhost:30001/snaps/{artefact.id}"

    def test_deb_url_generation(self, generator: DataGenerator):
        """Test URL generation for deb artefacts"""
        artefact = generator.gen_artefact(name="test-deb", version="1.0.0")
        artefact.family = FamilyName.deb
        url = get_artefact_url(artefact)
        assert url == f"http://localhost:30001/debs/{artefact.id}"

    def test_charm_url_generation(self, generator: DataGenerator):
        """Test URL generation for charm artefacts"""
        artefact = generator.gen_artefact(name="test-charm", version="1.0.0")
        artefact.family = FamilyName.charm
        url = get_artefact_url(artefact)
        assert url == f"http://localhost:30001/charms/{artefact.id}"

    def test_image_url_generation(self, generator: DataGenerator):
        """Test URL generation for image artefacts"""
        artefact = generator.gen_artefact(name="test-image", version="1.0.0")
        artefact.family = FamilyName.image
        url = get_artefact_url(artefact)
        assert url == f"http://localhost:30001/images/{artefact.id}"
