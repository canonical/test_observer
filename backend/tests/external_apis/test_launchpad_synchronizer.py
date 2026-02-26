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
from test_observer.external_apis.launchpad.launchpad_client import LaunchpadClient
from test_observer.external_apis.synchronizers.launchpad import (
    LaunchpadIssueSynchronizer,
)
from test_observer.external_apis.models import IssueData
from test_observer.data_access.models import Issue, IssueStatus, IssueSource
from sqlalchemy.orm import Session


def test_can_sync_launchpad_url():
    """Test that synchronizer recognizes Launchpad URLs"""
    mock_client = Mock(spec=LaunchpadClient)
    synchronizer = LaunchpadIssueSynchronizer(mock_client)

    issue = Mock()
    issue.url = "https://bugs.launchpad.net/ubuntu/+bug/123456"

    assert synchronizer.can_sync(issue) is True


def test_cannot_sync_non_launchpad_url():
    """Test that synchronizer rejects non-Launchpad URLs"""
    mock_client = Mock(spec=LaunchpadClient)
    synchronizer = LaunchpadIssueSynchronizer(mock_client)

    issue = Mock()
    issue.url = "https://github.com/canonical/test-repo/issues/123"

    assert synchronizer.can_sync(issue) is False


def test_cannot_sync_none_url():
    """Test that synchronizer rejects issues with no URL"""
    mock_client = Mock(spec=LaunchpadClient)
    synchronizer = LaunchpadIssueSynchronizer(mock_client)

    issue = Mock()
    issue.url = None

    assert synchronizer.can_sync(issue) is False


def test_sync_issue_updates_title_and_status(db_session: Session):
    """Test successful issue sync with updates"""
    # Mock the Launchpad client
    mock_client = Mock(spec=LaunchpadClient)

    # Mock the Launchpad issue response using IssueData
    mock_client.get_issue.return_value = IssueData(
        title="Updated Launchpad Bug",
        state="closed",
        state_reason="Fix Released",
        raw={"id": 123456},
    )

    # Create synchronizer with mocked client
    synchronizer = LaunchpadIssueSynchronizer(mock_client)

    # Create issue
    issue = Issue(
        source=IssueSource.LAUNCHPAD,
        project="ubuntu",
        key="123456",
        title="Old Title",
        status=IssueStatus.OPEN,
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    # Verify url is computed correctly
    assert "launchpad" in issue.url

    # Sync the issue
    result = synchronizer.sync_issue(issue, db_session)

    # Verify results
    assert result.success is True
    assert result.title_updated is True
    assert result.status_updated is True
    assert issue.title == "Updated Launchpad Bug"
    assert issue.status == IssueStatus.CLOSED

    # Verify client was called with project and key
    mock_client.get_issue.assert_called_once_with("ubuntu", "123456")


def test_sync_issue_no_changes(db_session: Session):
    """Test sync when issue is already up to date"""
    # Mock the Launchpad client
    mock_client = Mock(spec=LaunchpadClient)

    # Mock the Launchpad issue response (same as DB)
    mock_client.get_issue.return_value = IssueData(
        title="Same Title",
        state="open",
        state_reason="New",
        raw={"id": 654321},
    )

    # Create synchronizer
    synchronizer = LaunchpadIssueSynchronizer(mock_client)

    # Create test issue (already in sync)
    issue = Issue(
        source=IssueSource.LAUNCHPAD,
        project="ubuntu",
        key="654321",
        title="Same Title",
        status=IssueStatus.OPEN,
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    # Verify url is computed correctly
    assert "launchpad" in issue.url

    # Sync the issue
    result = synchronizer.sync_issue(issue, db_session)

    # Verify no changes
    assert result.success is True
    assert result.title_updated is False
    assert result.status_updated is False


def test_sync_issue_handles_error(db_session: Session):
    """Test error handling during sync"""
    # Mock the Launchpad client to raise an exception
    mock_client = Mock(spec=LaunchpadClient)
    mock_client.get_issue.side_effect = Exception("Launchpad API Error")

    # Create synchronizer
    synchronizer = LaunchpadIssueSynchronizer(mock_client)

    # Create test issue
    issue = Issue(
        source=IssueSource.LAUNCHPAD,
        project="ubuntu",
        key="999999",
        title="Test Bug",
        status=IssueStatus.OPEN,
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    # Verify url is computed correctly
    assert "launchpad" in issue.url

    # Sync the issue
    result = synchronizer.sync_issue(issue, db_session)

    # Verify error result
    assert result.success is False
    assert result.error is not None
    assert "Launchpad API Error" in result.error


def test_sync_issue_handles_different_projects(db_session: Session):
    """Test sync with different Launchpad projects"""
    # Mock the Launchpad client
    mock_client = Mock(spec=LaunchpadClient)

    # Mock the Launchpad issue response
    mock_client.get_issue.return_value = IssueData(
        title="Debian Bug",
        state="open",
        state_reason="New",
        raw={"id": 555555},
    )

    # Create synchronizer
    synchronizer = LaunchpadIssueSynchronizer(mock_client)

    # Create test issue for debian project
    issue = Issue(
        source=IssueSource.LAUNCHPAD,
        project="debian",
        key="555555",
        title="Old Title",
        status=IssueStatus.CLOSED,
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    # Verify url is computed correctly with debian project
    assert "launchpad" in issue.url

    # Sync the issue
    result = synchronizer.sync_issue(issue, db_session)

    # Verify results
    assert result.success is True
    assert result.title_updated is True
    assert result.status_updated is True
    assert issue.title == "Debian Bug"
    assert issue.status == IssueStatus.OPEN

    # Verify client was called with debian project
    mock_client.get_issue.assert_called_once_with("debian", "555555")
