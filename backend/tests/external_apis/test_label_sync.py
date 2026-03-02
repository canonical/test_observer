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

from sqlalchemy.orm import Session

from test_observer.data_access.models import Issue, IssueSource, IssueStatus
from test_observer.external_apis.github import GitHubClient
from test_observer.external_apis.jira import JiraClient
from test_observer.external_apis.launchpad import LaunchpadClient
from test_observer.external_apis.models import IssueData
from test_observer.external_apis.synchronizers.github import GitHubIssueSynchronizer
from test_observer.external_apis.synchronizers.jira import JiraIssueSynchronizer
from test_observer.external_apis.synchronizers.launchpad import (
    LaunchpadIssueSynchronizer,
)


def test_github_sync_adds_new_labels(db_session: Session):
    """Test that syncing adds labels to an issue without labels"""
    mock_client = Mock(spec=GitHubClient)
    mock_client.get_issue.return_value = IssueData(
        title="Test Issue",
        state="open",
        state_reason=None,
        labels=["bug", "enhancement", "priority-high"],
        raw={},
    )

    issue = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="123",
        title="Test Issue",
        status=IssueStatus.OPEN,
        labels=None,  # No labels initially
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    synchronizer = GitHubIssueSynchronizer(mock_client)
    result = synchronizer.sync_issue(issue, db_session)

    assert result.success is True
    assert result.labels_updated is True
    assert issue.labels == ["bug", "enhancement", "priority-high"]


def test_github_sync_updates_existing_labels(db_session: Session):
    """Test that syncing updates labels when they change"""
    mock_client = Mock(spec=GitHubClient)
    mock_client.get_issue.return_value = IssueData(
        title="Test Issue",
        state="open",
        state_reason=None,
        labels=["bug", "wontfix"],  # Changed labels
        raw={},
    )

    issue = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="123",
        title="Test Issue",
        status=IssueStatus.OPEN,
        labels=["bug", "enhancement"],  # Old labels
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    synchronizer = GitHubIssueSynchronizer(mock_client)
    result = synchronizer.sync_issue(issue, db_session)

    assert result.success is True
    assert result.labels_updated is True
    assert issue.labels == ["bug", "wontfix"]


def test_github_sync_no_label_changes(db_session: Session):
    """Test that syncing detects when labels haven't changed"""
    mock_client = Mock(spec=GitHubClient)
    mock_client.get_issue.return_value = IssueData(
        title="Test Issue",
        state="open",
        state_reason=None,
        labels=["bug", "enhancement"],
        raw={},
    )

    issue = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="123",
        title="Test Issue",
        status=IssueStatus.OPEN,
        labels=["enhancement", "bug"],
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    synchronizer = GitHubIssueSynchronizer(mock_client)
    result = synchronizer.sync_issue(issue, db_session)

    assert result.success is True
    assert result.labels_updated is False


def test_jira_sync_with_labels(db_session: Session):
    """Test Jira label synchronization"""
    mock_client = Mock(spec=JiraClient)
    mock_client.get_issue.return_value = IssueData(
        title="Jira Issue",
        state="open",
        state_reason="To Do",
        labels=["backend", "database", "urgent"],
        raw={},
    )

    issue = Issue(
        source=IssueSource.JIRA,
        project="warthogs.atlassian.net",
        key="TO-123",
        title="Jira Issue",
        status=IssueStatus.OPEN,
        labels=None,
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    synchronizer = JiraIssueSynchronizer(mock_client)
    result = synchronizer.sync_issue(issue, db_session)

    assert result.success is True
    assert result.labels_updated is True
    assert issue.labels == ["backend", "database", "urgent"]


def test_launchpad_sync_with_labels(db_session: Session):
    """Test Launchpad label synchronization"""
    mock_client = Mock(spec=LaunchpadClient)
    mock_client.get_issue.return_value = IssueData(
        title="Launchpad Bug",
        state="open",
        state_reason="New",
        labels=["kernel", "regression", "focal"],
        raw={},
    )

    issue = Issue(
        source=IssueSource.LAUNCHPAD,
        project="ubuntu",
        key="2000000",
        title="Launchpad Bug",
        status=IssueStatus.OPEN,
        labels=[],  # Empty labels
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    synchronizer = LaunchpadIssueSynchronizer(mock_client)
    result = synchronizer.sync_issue(issue, db_session)

    assert result.success is True
    assert result.labels_updated is True
    assert issue.labels == ["focal", "kernel", "regression"]  # Sorted


def test_sync_removes_all_labels(db_session: Session):
    """Test that syncing correctly handles label removal"""
    mock_client = Mock(spec=GitHubClient)
    mock_client.get_issue.return_value = IssueData(
        title="Test Issue",
        state="closed",
        state_reason="completed",
        labels=[],  # All labels removed
        raw={},
    )

    issue = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="123",
        title="Test Issue",
        status=IssueStatus.OPEN,
        labels=["bug", "wontfix"],
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    synchronizer = GitHubIssueSynchronizer(mock_client)
    result = synchronizer.sync_issue(issue, db_session)

    assert result.success is True
    assert result.labels_updated is True
    assert issue.labels == []
