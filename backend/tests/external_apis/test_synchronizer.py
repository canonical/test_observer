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
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from test_observer.external_apis.synchronizer import IssueSynchronizer
from test_observer.external_apis.models import IssueData
from test_observer.data_access.models import Issue
from test_observer.data_access.models_enums import IssueSource, IssueStatus
from test_observer.external_apis.exceptions import IssueNotFoundError, APIError


# Mock environment variables for all tests
@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for IssueSynchronizer initialization"""
    env_vars = {
        "GITHUB_TOKEN": "test-github-token",
        "JIRA_BASE_URL": "https://test.atlassian.net",
        "JIRA_EMAIL": "test@example.com",
        "JIRA_API_TOKEN": "test-jira-token",
        "LAUNCHPAD_ANONYMOUS": "true",
    }
    with patch.dict("os.environ", env_vars):
        yield


class TestIssueSynchronizer:
    """Integration tests for IssueSynchronizer"""

    def test_sync_issue_github_with_title_update(self, db_session: Session):
        """Test syncing a GitHub issue with empty title"""
        # Create test issue with empty title
        issue = Issue(
            source=IssueSource.GITHUB,
            project="canonical/test_observer",
            key="71",
            title="",
            status=IssueStatus.UNKNOWN,
        )
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)

        # Mock GitHub client
        with patch("test_observer.external_apis.synchronizer.GitHubClient"):
            mock_client = Mock()
            mock_client.get_issue.return_value = IssueData(
                title="Fix filter functionality",
                state="open",
                state_reason="open",
                raw={"id": 123},
            )

            synchronizer = IssueSynchronizer()
            synchronizer.github_client = mock_client
            result = synchronizer.sync_issue(db_session, issue)

        assert result.success is True
        assert result.title_updated is True
        assert result.status_updated is True
        assert issue.title == "Fix filter functionality"
        assert issue.status == IssueStatus.OPEN

    def test_sync_issue_jira_with_title_update(self, db_session: Session):
        """Test syncing a Jira issue"""
        issue = Issue(
            source=IssueSource.JIRA,
            project="TO",
            key="255",
            title="",
            status=IssueStatus.UNKNOWN,
        )
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)

        with patch("test_observer.external_apis.synchronizer.JiraClient"):
            mock_client = Mock()
            mock_client.get_issue.return_value = IssueData(
                title="Build synchronization architecture",
                state="open",
                state_reason="To Do",
                raw={"id": "TO-255"},
            )

            synchronizer = IssueSynchronizer()
            synchronizer.jira_client = mock_client
            result = synchronizer.sync_issue(db_session, issue)

        assert result.success is True
        assert result.title_updated is True
        assert issue.title == "Build synchronization architecture"
        assert issue.status == IssueStatus.OPEN

    def test_sync_issue_launchpad_with_title_update(self, db_session: Session):
        """Test syncing a Launchpad issue"""
        issue = Issue(
            source=IssueSource.LAUNCHPAD,
            project="ubuntu",
            key="2000000",
            title="",
            status=IssueStatus.UNKNOWN,
        )
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)

        with patch("test_observer.external_apis.synchronizer.LaunchpadClient"):
            mock_client = Mock()
            mock_client.get_issue.return_value = IssueData(
                title="Multiple instances of Python object-testing mistakes",
                state="open",
                state_reason="New",
                raw={"id": 2000000},
            )

            synchronizer = IssueSynchronizer()
            synchronizer.launchpad_client = mock_client
            result = synchronizer.sync_issue(db_session, issue)

        assert result.success is True
        assert result.title_updated is True
        assert issue.title == "Multiple instances of Python object-testing mistakes"

    def test_sync_issue_no_changes_needed(self, db_session: Session):
        """Test syncing when issue already has correct data"""
        issue = Issue(
            source=IssueSource.GITHUB,
            project="canonical/test_observer",
            key="71",
            title="Fix filter functionality",
            status=IssueStatus.OPEN,
        )
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)

        with patch("test_observer.external_apis.synchronizer.GitHubClient"):
            mock_client = Mock()
            mock_client.get_issue.return_value = IssueData(
                title="Fix filter functionality",
                state="open",
                state_reason="open",
                raw={"id": 123},
            )

            synchronizer = IssueSynchronizer()
            synchronizer.github_client = mock_client
            result = synchronizer.sync_issue(db_session, issue)

        assert result.success is True
        assert result.title_updated is False
        assert result.status_updated is False

    def test_sync_issue_status_update_only(self, db_session: Session):
        """Test syncing when only status changes"""
        issue = Issue(
            source=IssueSource.GITHUB,
            project="canonical/test_observer",
            key="71",
            title="Fix filter functionality",
            status=IssueStatus.OPEN,
        )
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)

        with patch("test_observer.external_apis.synchronizer.GitHubClient"):
            mock_client = Mock()
            mock_client.get_issue.return_value = IssueData(
                title="Fix filter functionality",
                state="closed",
                state_reason="completed",
                raw={"id": 123},
            )

            synchronizer = IssueSynchronizer()
            synchronizer.github_client = mock_client
            result = synchronizer.sync_issue(db_session, issue)

        assert result.success is True
        assert result.title_updated is False
        assert result.status_updated is True
        assert issue.status == IssueStatus.CLOSED

    def test_sync_issue_not_found_error(self, db_session: Session):
        """Test sync when issue is not found on API (404)"""
        issue = Issue(
            source=IssueSource.GITHUB,
            project="canonical/charm-integration-testing",
            key="129",
            title="",
            status=IssueStatus.UNKNOWN,
        )
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)

        with patch("test_observer.external_apis.synchronizer.GitHubClient"):
            mock_client = Mock()
            mock_client.get_issue.side_effect = IssueNotFoundError("Issue not found")

            synchronizer = IssueSynchronizer()
            synchronizer.github_client = mock_client
            result = synchronizer.sync_issue(db_session, issue)

        assert result.success is False
        assert result.title_updated is False
        assert result.error is not None
        assert "not found" in result.error.lower()
        # Database should not be updated
        db_session.refresh(issue)
        assert issue.title == ""

    def test_sync_issue_api_error(self, db_session: Session):
        """Test sync when API returns an error"""
        issue = Issue(
            source=IssueSource.GITHUB,
            project="canonical/test_observer",
            key="71",
            title="",
            status=IssueStatus.UNKNOWN,
        )
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)

        with patch("test_observer.external_apis.synchronizer.GitHubClient"):
            mock_client = Mock()
            mock_client.get_issue.side_effect = APIError("Rate limited")

            synchronizer = IssueSynchronizer()
            synchronizer.github_client = mock_client
            result = synchronizer.sync_issue(db_session, issue)

        assert result.success is False
        assert result.error is not None
        assert "API error" in result.error

    def test_sync_all_issues_multiple_sources(self, db_session: Session):
        """Test syncing issues from different sources"""
        # Create test issues from different sources
        github_issue = Issue(
            source=IssueSource.GITHUB,
            project="canonical/test_observer",
            key="71",
            title="",
            status=IssueStatus.UNKNOWN,
        )
        jira_issue = Issue(
            source=IssueSource.JIRA,
            project="TO",
            key="255",
            title="",
            status=IssueStatus.UNKNOWN,
        )
        launchpad_issue = Issue(
            source=IssueSource.LAUNCHPAD,
            project="ubuntu",
            key="2000000",
            title="",
            status=IssueStatus.UNKNOWN,
        )
        db_session.add_all([github_issue, jira_issue, launchpad_issue])
        db_session.commit()

        with (
            patch("test_observer.external_apis.synchronizer.GitHubClient"),
            patch("test_observer.external_apis.synchronizer.JiraClient"),
            patch("test_observer.external_apis.synchronizer.LaunchpadClient"),
        ):
            synchronizer = IssueSynchronizer()

            # Mock GitHub client
            synchronizer.github_client.get_issue.return_value = IssueData(
                title="GitHub Issue Title",
                state="open",
                state_reason="open",
                raw={"id": 123},
            )

            # Mock Jira client
            synchronizer.jira_client.get_issue.return_value = IssueData(
                title="Jira Issue Title",
                state="closed",
                state_reason="Done",
                raw={"id": "TO-255"},
            )

            # Mock Launchpad client
            synchronizer.launchpad_client.get_issue.return_value = IssueData(
                title="Launchpad Issue Title",
                state="open",
                state_reason="New",
                raw={"id": 2000000},
            )

            results = synchronizer.sync_all_issues(db_session)

        assert results.total == 3
        assert results.successful == 3
        assert results.failed == 0
        assert results.updated == 3
        assert results.success_rate == 100.0

        # Verify all issues were updated
        db_session.refresh(github_issue)
        db_session.refresh(jira_issue)
        db_session.refresh(launchpad_issue)

        assert github_issue.title == "GitHub Issue Title"
        assert github_issue.status == IssueStatus.OPEN
        assert jira_issue.title == "Jira Issue Title"
        assert jira_issue.status == IssueStatus.CLOSED
        assert launchpad_issue.title == "Launchpad Issue Title"

    def test_sync_all_issues_mixed_success_and_failure(self, db_session: Session):
        """Test syncing with some success and some failures"""
        # Create issues
        issue1 = Issue(
            source=IssueSource.GITHUB,
            project="canonical/test_observer",
            key="71",
            title="",
            status=IssueStatus.UNKNOWN,
        )
        issue2 = Issue(
            source=IssueSource.GITHUB,
            project="canonical/charm-integration-testing",
            key="129",
            title="",
            status=IssueStatus.UNKNOWN,
        )
        issue3 = Issue(
            source=IssueSource.JIRA,
            project="TO",
            key="255",
            title="",
            status=IssueStatus.UNKNOWN,
        )
        db_session.add_all([issue1, issue2, issue3])
        db_session.commit()

        with (
            patch("test_observer.external_apis.synchronizer.GitHubClient"),
            patch("test_observer.external_apis.synchronizer.JiraClient"),
        ):
            synchronizer = IssueSynchronizer()

            # First GitHub issue succeeds
            # Second GitHub issue fails (404)
            # Jira issue succeeds
            def github_side_effect(_project: str, key: str) -> IssueData:
                if key == "129":
                    raise IssueNotFoundError("Issue not found")
                return IssueData(
                    title="GitHub Issue",
                    state="open",
                    state_reason="open",
                    raw={"id": 123},
                )

            synchronizer.github_client.get_issue.side_effect = github_side_effect
            synchronizer.jira_client.get_issue.return_value = IssueData(
                title="Jira Issue",
                state="open",
                state_reason="To Do",
                raw={"id": "TO-255"},
            )

            results = synchronizer.sync_all_issues(db_session)

        assert results.total == 3
        assert results.successful == 2
        assert results.failed == 1
        assert results.updated == 2
        assert results.success_rate == pytest.approx(66.67, 0.1)

    def test_sync_all_issues_empty_database(self, db_session: Session):
        """Test syncing when database has no issues"""
        synchronizer = IssueSynchronizer()
        results = synchronizer.sync_all_issues(db_session)

        assert results.total == 0
        assert results.successful == 0
        assert results.failed == 0
        assert results.updated == 0
        assert results.success_rate == 0.0

    def test_sync_issue_with_unknown_status_mapping(self, db_session: Session):
        """Test that unknown states are mapped to UNKNOWN status"""
        issue = Issue(
            source=IssueSource.JIRA,
            project="TO",
            key="255",
            title="Test",
            status=IssueStatus.UNKNOWN,
        )
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)

        with patch("test_observer.external_apis.synchronizer.JiraClient"):
            mock_client = Mock()
            mock_client.get_issue.return_value = IssueData(
                title="Test",
                state="in_progress",  # Unknown state
                state_reason="In Progress",
                raw={"id": "TO-255"},
            )

            synchronizer = IssueSynchronizer()
            synchronizer.jira_client = mock_client
            result = synchronizer.sync_issue(db_session, issue)

        assert result.success is True
        assert issue.status == IssueStatus.UNKNOWN  # Maps to UNKNOWN

    def test_sync_updates_database_correctly(self, db_session: Session):
        """Test that database is updated correctly and changes are persisted"""
        issue = Issue(
            source=IssueSource.GITHUB,
            project="canonical/test_observer",
            key="71",
            title="Old Title",
            status=IssueStatus.CLOSED,
        )
        db_session.add(issue)
        db_session.commit()
        issue_id = issue.id

        with patch("test_observer.external_apis.synchronizer.GitHubClient"):
            mock_client = Mock()
            mock_client.get_issue.return_value = IssueData(
                title="New Title",
                state="open",
                state_reason="open",
                raw={"id": 123},
            )

            synchronizer = IssueSynchronizer()
            synchronizer.github_client = mock_client
            synchronizer.sync_issue(db_session, issue)

        # Verify changes persisted to database
        db_session.expunge_all()
        refreshed_issue = db_session.query(Issue).filter_by(id=issue_id).first()

        assert refreshed_issue is not None
        assert refreshed_issue.title == "New Title"
        assert refreshed_issue.status == IssueStatus.OPEN

    def test_sync_issue_idempotent(self, db_session: Session):
        """Test that syncing multiple times produces same result"""
        issue = Issue(
            source=IssueSource.GITHUB,
            project="canonical/test_observer",
            key="71",
            title="",
            status=IssueStatus.UNKNOWN,
        )
        db_session.add(issue)
        db_session.commit()

        issue_data = IssueData(
            title="Test Title",
            state="open",
            state_reason="open",
            raw={"id": 123},
        )

        with patch("test_observer.external_apis.synchronizer.GitHubClient"):
            mock_client = Mock()
            mock_client.get_issue.return_value = issue_data

            synchronizer = IssueSynchronizer()
            synchronizer.github_client = mock_client

            # Sync first time
            result1 = synchronizer.sync_issue(db_session, issue)
            first_title = issue.title
            first_status = issue.status

            # Sync second time
            result2 = synchronizer.sync_issue(db_session, issue)
            second_title = issue.title
            second_status = issue.status

        # Both syncs should succeed but second should have no updates
        assert result1.success is True
        assert result2.success is True
        assert result1.title_updated is True
        assert result2.title_updated is False
        assert result1.status_updated is True
        assert result2.status_updated is False

        # Results should be identical
        assert first_title == second_title
        assert first_status == second_status
