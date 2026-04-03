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
from test_observer.external_apis.issue_creator import IssueCreator, JiraIssueContext
from tests.data_generator import DataGenerator


class TestCreateIssue:
    """Test create_issue method"""

    def test_create_issue_with_jira_client(self):
        """Test creating issue with Jira client"""
        mock_jira = Mock()
        jira_ctx = JiraIssueContext.model_construct(client=mock_jira, parent_issue="TO-123")
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
            assignee=None,
        )

    def test_create_issue_forwards_assignee(self):
        """Test that assignee is forwarded to Jira client"""
        mock_jira = Mock()
        jira_ctx = JiraIssueContext.model_construct(client=mock_jira, parent_issue="TO-123")
        creator = IssueCreator(jira_ctx=jira_ctx)

        creator.create_issue(
            summary="Test Issue",
            description="Test description",
            assignee="alice-handle",
        )

        mock_jira.create_issue.assert_called_once_with(
            project_key="TO",
            summary="Test Issue",
            issue_type="Task",
            description="Test description",
            parent_issue_key="TO-123",
            assignee="alice-handle",
        )

    def test_create_issue_with_no_clients_raises_error(self):
        """Test creating issue with no clients raises ValueError"""
        creator = IssueCreator()

        with pytest.raises(ValueError, match="No issue creation context configured"):
            creator.create_issue(
                summary="Test Issue",
                description="Test description",
            )

    def test_create_issue_without_jira_context_raises_error(self):
        """Test creating issue without jira_ctx raises ValueError"""
        creator = IssueCreator(jira_ctx=None)

        with pytest.raises(ValueError, match="No issue creation context configured"):
            creator.create_issue(
                summary="Test Issue",
                description="Test description",
            )


class TestCreateReviewIssues:
    """Test create_review_issues method"""

    def test_create_review_issues_success(self, generator: DataGenerator):
        """Test successful creation of review issues"""
        mock_jira = Mock()
        jira_ctx = JiraIssueContext.model_construct(client=mock_jira, parent_issue="TO-123")
        reviewer = generator.gen_user(name="Alice", email="alice@example.com", launchpad_handle="alice-lp")
        artefact = generator.gen_artefact(
            name="test-snap",
            version="1.0.0",
            reviewers=[reviewer],
        )

        creator = IssueCreator(jira_ctx=jira_ctx)
        creator.create_review_issues(artefact, reviewer)

        # Should call create_issue twice via Jira client
        assert mock_jira.create_issue.call_count == 2

        expected_artefact_url = get_artefact_url(artefact)

        # First call: artefact review
        first_call = mock_jira.create_issue.call_args_list[0]
        assert first_call.kwargs["project_key"] == "TO"
        assert first_call.kwargs["summary"] == "Review artefact test-snap version 1.0.0 - Alice"
        assert (
            first_call.kwargs["description"]
            == f"Review artefact test-snap version 1.0.0\n\nArtefact page: {expected_artefact_url}"
        )
        assert first_call.kwargs["issue_type"] == "Task"
        assert first_call.kwargs["parent_issue_key"] == "TO-123"
        assert first_call.kwargs["assignee"] == "alice-lp"

        # Second call: environment review
        second_call = mock_jira.create_issue.call_args_list[1]
        assert second_call.kwargs["project_key"] == "TO"
        assert second_call.kwargs["summary"] == "Review environments of Artefact test-snap version 1.0.0 - Alice"
        assert second_call.kwargs["description"] == (
            f"Review test environments for artefact test-snap version 1.0.0\n\nArtefact page: {expected_artefact_url}"
        )
        assert second_call.kwargs["issue_type"] == "Task"
        assert second_call.kwargs["parent_issue_key"] == "TO-123"
        assert second_call.kwargs["assignee"] == "alice-lp"

    def test_create_review_issues_reviewer_without_launchpad_handle(self, generator: DataGenerator):
        """Test that issues are created without assignee when reviewer has no launchpad handle"""
        mock_jira = Mock()
        jira_ctx = JiraIssueContext.model_construct(client=mock_jira, parent_issue="TO-123")
        reviewer = generator.gen_user(name="Alice", email="alice@example.com", launchpad_handle=None)
        artefact = generator.gen_artefact(
            name="test-snap",
            version="1.0.0",
            reviewers=[reviewer],
        )

        creator = IssueCreator(jira_ctx=jira_ctx)
        creator.create_review_issues(artefact, reviewer)

        assert mock_jira.create_issue.call_count == 2
        for call in mock_jira.create_issue.call_args_list:
            assert call.kwargs["assignee"] is None

    def test_create_review_issues_no_reviewers(self, generator: DataGenerator):
        """Test that ValueError is raised when artefact has no reviewers"""
        mock_jira = Mock()
        jira_ctx = JiraIssueContext.model_construct(client=mock_jira, parent_issue="TO-123")
        reviewer = generator.gen_user(name="Alice", email="alice@example.com")
        artefact = generator.gen_artefact(
            name="test-snap",
            version="1.0.0",
            reviewers=[],
        )

        creator = IssueCreator(jira_ctx=jira_ctx)

        with pytest.raises(ValueError, match="has no reviewers assigned"):
            creator.create_review_issues(artefact, reviewer)

        mock_jira.create_issue.assert_not_called()

    def test_create_review_issues_invalid_reviewer(self, generator: DataGenerator):
        """Test that ValueError is raised when reviewer is not in artefact's reviewer list"""
        mock_jira = Mock()
        jira_ctx = JiraIssueContext.model_construct(client=mock_jira, parent_issue="TO-123")
        valid_reviewer = generator.gen_user(name="Alice", email="alice@example.com")
        invalid_reviewer = generator.gen_user(name="Bob", email="bob@example.com")
        artefact = generator.gen_artefact(
            name="test-snap",
            version="1.0.0",
            reviewers=[valid_reviewer],
        )

        creator = IssueCreator(jira_ctx=jira_ctx)

        with pytest.raises(ValueError, match="reviewers do not include"):
            creator.create_review_issues(artefact, invalid_reviewer)

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
        from test_observer.data_access.models_enums import FamilyName

        artefact = generator.gen_artefact(name="test-deb", version="1.0.0")
        artefact.family = FamilyName.deb
        url = get_artefact_url(artefact)
        assert url == f"http://localhost:30001/debs/{artefact.id}"

    def test_charm_url_generation(self, generator: DataGenerator):
        """Test URL generation for charm artefacts"""
        from test_observer.data_access.models_enums import FamilyName

        artefact = generator.gen_artefact(name="test-charm", version="1.0.0")
        artefact.family = FamilyName.charm
        url = get_artefact_url(artefact)
        assert url == f"http://localhost:30001/charms/{artefact.id}"

    def test_image_url_generation(self, generator: DataGenerator):
        """Test URL generation for image artefacts"""
        from test_observer.data_access.models_enums import FamilyName

        artefact = generator.gen_artefact(name="test-image", version="1.0.0")
        artefact.family = FamilyName.image
        url = get_artefact_url(artefact)
        assert url == f"http://localhost:30001/images/{artefact.id}"
