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

from unittest.mock import MagicMock, Mock

from sqlalchemy.orm import Session

from test_observer.data_access.models import Issue, IssueSource, IssueStatus
from test_observer.external_apis.github import GitHubClient
from test_observer.external_apis.synchronizers.github import GitHubIssueSynchronizer


def test_can_sync_github_url():
    """Test that synchronizer recognizes GitHub URLs"""
    mock_client = Mock(spec=GitHubClient)
    synchronizer = GitHubIssueSynchronizer(mock_client)

    # Create a mock issue with GitHub URL
    issue = Mock()
    issue.url = "https://github.com/canonical/test-repo/issues/123"

    assert synchronizer.can_sync(issue) is True


def test_cannot_sync_non_github_url():
    """Test that synchronizer rejects non-GitHub URLs"""
    mock_client = Mock(spec=GitHubClient)
    synchronizer = GitHubIssueSynchronizer(mock_client)

    issue = Mock()
    issue.url = "https://launchpad.net/bugs/123"

    assert synchronizer.can_sync(issue) is False


def test_cannot_sync_none_url():
    """Test that synchronizer rejects issues with no URL"""
    mock_client = Mock(spec=GitHubClient)
    synchronizer = GitHubIssueSynchronizer(mock_client)

    issue = Mock()
    issue.url = None

    assert synchronizer.can_sync(issue) is False


def test_sync_issue_updates_title_and_status(db_session: Session) -> None:
    """Test successful issue sync with updates"""
    # Create issue
    issue = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="123",
        title="Old Title",
        status=IssueStatus.OPEN,
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    # Verify url is computed correctly
    assert "github.com" in issue.url

    # Mock the GitHub client
    mock_client = Mock(spec=GitHubClient)

    # Mock the GitHub issue response
    mock_gh_issue = MagicMock()
    mock_gh_issue.title = "Updated Issue Title"
    mock_gh_issue.state = "closed"
    mock_client.get_issue.return_value = mock_gh_issue

    # Create synchronizer with mocked client
    synchronizer = GitHubIssueSynchronizer(mock_client)

    # Sync the issue
    result = synchronizer.sync_issue(issue, db_session)

    # Verify results
    assert result.success is True
    assert result.title_updated is True
    assert result.status_updated is True
    assert issue.title == "Updated Issue Title"
    assert issue.status == IssueStatus.CLOSED

    # Verify client was called with project and key
    mock_client.get_issue.assert_called_once_with("canonical/test-repo", "123")


def test_sync_issue_no_changes(db_session: Session):
    """Test sync when issue is already up to date"""
    # Mock the GitHub client
    mock_client = Mock(spec=GitHubClient)

    # Mock the GitHub issue response (same as DB)
    mock_gh_issue = MagicMock()
    mock_gh_issue.title = "Same Title"
    mock_gh_issue.state = "open"
    mock_client.get_issue.return_value = mock_gh_issue

    # Create synchronizer
    synchronizer = GitHubIssueSynchronizer(mock_client)

    # Create test issue (already in sync)
    issue = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="456",
        title="Same Title",
        status=IssueStatus.OPEN,
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    # Verify url is computed correctly
    assert "github.com" in issue.url

    # Sync the issue
    result = synchronizer.sync_issue(issue, db_session)

    # Verify no changes
    assert result.success is True
    assert result.title_updated is False
    assert result.status_updated is False


def test_sync_issue_handles_error(db_session: Session):
    """Test error handling during sync"""
    # Mock the GitHub client to raise an exception
    mock_client = Mock(spec=GitHubClient)
    mock_client.get_issue.side_effect = Exception("API Error")

    # Create synchronizer
    synchronizer = GitHubIssueSynchronizer(mock_client)

    # Create test issue
    issue = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="789",
        title="Test Issue",
        status=IssueStatus.OPEN,
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    # Verify url is computed correctly
    assert "github.com" in issue.url

    # Sync the issue
    result = synchronizer.sync_issue(issue, db_session)

    # Verify error result
    assert result.success is False
    assert result.error is not None
    assert "API Error" in result.error
