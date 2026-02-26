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
from test_observer.external_apis.jira.jira_client import JiraClient
from test_observer.external_apis.synchronizers.jira import JiraIssueSynchronizer
from test_observer.data_access.models import Issue, IssueStatus, IssueSource
from test_observer.external_apis.models import IssueData
from sqlalchemy.orm import Session


def test_can_sync_jira_url():
    """Test that synchronizer recognizes Jira URLs"""
    mock_client = Mock(spec=JiraClient)
    synchronizer = JiraIssueSynchronizer(mock_client)

    # Create a mock issue with Jira URL
    issue = Mock()
    issue.url = "https://warthogs.atlassian.net/browse/TO-123"

    assert synchronizer.can_sync(issue) is True


def test_can_sync_jira_url_with_jira_keyword():
    """Test that synchronizer recognizes URLs with 'jira' in them"""
    mock_client = Mock(spec=JiraClient)
    synchronizer = JiraIssueSynchronizer(mock_client)

    issue = Mock()
    issue.url = "https://jira.company.com/browse/PROJECT-123"

    assert synchronizer.can_sync(issue) is True


def test_cannot_sync_non_jira_url():
    """Test that synchronizer rejects non-Jira URLs"""
    mock_client = Mock(spec=JiraClient)
    synchronizer = JiraIssueSynchronizer(mock_client)

    issue = Mock()
    issue.url = "https://github.com/canonical/test-repo/issues/123"

    assert synchronizer.can_sync(issue) is False


def test_cannot_sync_none_url():
    """Test that synchronizer rejects issues with no URL"""
    mock_client = Mock(spec=JiraClient)
    synchronizer = JiraIssueSynchronizer(mock_client)

    issue = Mock()
    issue.url = None

    assert synchronizer.can_sync(issue) is False


def test_sync_issue_updates_title_and_status(db_session: Session) -> None:
    """Test successful issue sync with updates"""
    # Create issue
    issue = Issue(
        source=IssueSource.JIRA,
        project="warthogs.atlassian.net",
        key="TO-123",
        title="Old Title",
        status=IssueStatus.OPEN,
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    assert "jira" in issue.url or "atlassian" in issue.url

    # Mock the Jira client
    mock_client = Mock(spec=JiraClient)

    # Mock the Jira client to return IssueData (not raw Jira Issue)
    mock_client.get_issue.return_value = IssueData(
        title="Updated Jira Issue",
        state="closed",
        state_reason="Done",
        raw={"key": "TO-123"},
    )

    synchronizer = JiraIssueSynchronizer(mock_client)

    result = synchronizer.sync_issue(issue, db_session)

    # Verify results
    assert result.success is True
    assert result.title_updated is True
    assert result.status_updated is True
    assert issue.title == "Updated Jira Issue"
    assert issue.status == IssueStatus.CLOSED

    mock_client.get_issue.assert_called_once_with("warthogs.atlassian.net", "TO-123")


def test_sync_issue_no_changes(db_session: Session) -> None:
    """Test sync when issue is already up to date"""
    # Create issue (already in sync)
    issue = Issue(
        source=IssueSource.JIRA,
        project="warthogs.atlassian.net",
        key="TO-456",
        title="Same Title",
        status=IssueStatus.OPEN,
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    assert "jira" in issue.url or "atlassian" in issue.url

    # Mock the Jira client
    mock_client = Mock(spec=JiraClient)

    # Mock the Jira client to return IssueData (not raw Jira Issue)
    mock_client.get_issue.return_value = IssueData(
        title="Same Title",
        state="open",
        state_reason="To Do",
        raw={"key": "TO-456"},
    )

    synchronizer = JiraIssueSynchronizer(mock_client)

    result = synchronizer.sync_issue(issue, db_session)

    # Verify no changes
    assert result.success is True
    assert result.title_updated is False
    assert result.status_updated is False


def test_sync_issue_handles_error(db_session: Session):
    """Test error handling during sync"""
    # Mock the Jira client to raise an exception
    mock_client = Mock(spec=JiraClient)
    mock_client.get_issue.side_effect = Exception("Jira API Error")

    # Create synchronizer
    synchronizer = JiraIssueSynchronizer(mock_client)

    # Create test issue
    issue = Issue(
        source=IssueSource.JIRA,
        project="warthogs.atlassian.net",
        key="TO-789",
        title="Test Issue",
        status=IssueStatus.OPEN,
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    # Verify url is computed correctly
    assert "jira" in issue.url or "atlassian" in issue.url

    # Sync the issue
    result = synchronizer.sync_issue(issue, db_session)

    # Verify error result
    assert result.success is False
    assert result.error is not None
    assert "Jira API Error" in result.error


def test_sync_issue_in_progress_maps_to_open(db_session: Session) -> None:
    """Test that 'In Progress' status maps to OPEN (not closed)"""
    # Create test issue that starts as CLOSED
    issue = Issue(
        source=IssueSource.JIRA,
        project="warthogs.atlassian.net",
        key="TO-999",
        title="Old Title",
        status=IssueStatus.CLOSED,
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    # Mock the Jira client
    mock_client = Mock(spec=JiraClient)

    # Mock the Jira client to return IssueData with in_progress state
    mock_client.get_issue.return_value = IssueData(
        title="In Progress Issue",
        state="in_progress",
        state_reason="In Progress",
        raw={"key": "TO-999"},
    )

    synchronizer = JiraIssueSynchronizer(mock_client)

    result = synchronizer.sync_issue(issue, db_session)

    # Verify "In Progress" maps to OPEN
    assert result.success is True
    assert result.status_updated is True
    assert issue.status == IssueStatus.OPEN
