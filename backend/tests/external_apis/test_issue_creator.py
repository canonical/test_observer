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
        jira_ctx = JiraIssueContext(client=mock_jira, parent_issue="TO-123")
        reviewer = generator.gen_user(name="Alice", email="alice@example.com")
        artefact = generator.gen_artefact(
            name="test-snap",
            version="1.0.0",
            reviewers=[reviewer],
        )

        creator = IssueCreator(jira_ctx=jira_ctx)
        creator.create_review_issues(artefact, reviewer)

        # Should call create_issue twice via Jira client
        assert mock_jira.create_issue.call_count == 2

        # First call: artefact review
        first_call = mock_jira.create_issue.call_args_list[0]
        assert first_call.kwargs["project_key"] == "TO"
        assert first_call.kwargs["summary"] == "Review artefact test-snap version 1.0.0 - Alice"
        assert first_call.kwargs["description"] == "Review artefact test-snap version 1.0.0"
        assert first_call.kwargs["issue_type"] == "Task"
        assert first_call.kwargs["parent_issue_key"] == "TO-123"

        # Second call: environment review
        second_call = mock_jira.create_issue.call_args_list[1]
        assert second_call.kwargs["project_key"] == "TO"
        assert second_call.kwargs["summary"] == "Review environments of Artefact test-snap version 1.0.0 - Alice"
        assert second_call.kwargs["description"] == "Review test environments for artefact test-snap version 1.0.0"
        assert second_call.kwargs["issue_type"] == "Task"
        assert second_call.kwargs["parent_issue_key"] == "TO-123"

    def test_create_review_issues_no_reviewers(self, generator: DataGenerator):
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

        with pytest.raises(ValueError, match="has no reviewers assigned"):
            creator.create_review_issues(artefact, reviewer)

        mock_jira.create_issue.assert_not_called()

    def test_create_review_issues_invalid_reviewer(self, generator: DataGenerator):
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

        with pytest.raises(ValueError, match="reviewers do not include"):
            creator.create_review_issues(artefact, invalid_reviewer)

        mock_jira.create_issue.assert_not_called()
