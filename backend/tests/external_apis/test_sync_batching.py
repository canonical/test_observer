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
from test_observer.external_apis.synchronizers.base import (
    BaseIssueSynchronizer,
    SyncResult,
)
from test_observer.external_apis.synchronizers.service import (
    IssueSynchronizationService,
)


def test_sync_issue_returns_success(db_session: Session) -> None:
    """Test that successful sync returns a successful SyncResult"""
    # Create issue
    issue = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="123",
        title="Test Issue",
        status=IssueStatus.OPEN,
        last_synced_at=None,
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    # Mock synchronizer
    mock_sync = Mock(spec=BaseIssueSynchronizer)
    mock_sync.can_sync.return_value = True
    mock_sync.fetch_issue_update.return_value = SyncResult(success=True)

    # Create service and sync — service does HTTP only, no DB writes
    service = IssueSynchronizationService([mock_sync])
    result = service.sync_issue(issue)

    assert result.success is True
    # last_synced_at is written at task level, not service level
    db_session.refresh(issue)
    assert issue.last_synced_at is None


def test_sync_issue_does_not_update_on_failure(db_session: Session) -> None:
    """Test that failed sync returns a failure SyncResult"""
    # Create issue
    issue = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="123",
        title="Test Issue",
        status=IssueStatus.OPEN,
        last_synced_at=None,
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    # Mock synchronizer to fail
    mock_sync = Mock(spec=BaseIssueSynchronizer)
    mock_sync.can_sync.return_value = True
    mock_sync.fetch_issue_update.return_value = SyncResult(success=False, error="API Error")

    # Create service and sync
    service = IssueSynchronizationService([mock_sync])
    result = service.sync_issue(issue)

    assert result.success is False
    assert result.error == "API Error"


def test_sync_issues_batch(db_session: Session) -> None:
    """Test syncing a batch of issues"""
    # Create multiple issues
    issues = []
    for i in range(5):
        issue = Issue(
            source=IssueSource.GITHUB,
            project="canonical/test-repo",
            key=str(i),
            title=f"Issue {i}",
            status=IssueStatus.OPEN,
            last_synced_at=None,
        )
        db_session.add(issue)
        issues.append(issue)
    db_session.commit()

    # Mock synchronizer
    mock_sync = Mock(spec=BaseIssueSynchronizer)
    mock_sync.can_sync.return_value = True
    mock_sync.fetch_issue_update.return_value = SyncResult(success=True, new_title="Updated Title")

    # Create service and sync batch
    service = IssueSynchronizationService([mock_sync])
    results = service.sync_issues_batch(issues)

    # Verify results
    assert results.total == 5
    assert results.successful == 5
    assert results.updated == 5
    assert results.failed == 0

    # last_synced_at is written at task level, not service level


def test_sync_issues_batch_mixed_results(db_session: Session) -> None:
    """Test batch sync with some successes and some failures"""
    # Create multiple issues
    issues = []
    for i in range(3):
        issue = Issue(
            source=IssueSource.GITHUB,
            project="canonical/test-repo",
            key=str(i),
            title=f"Issue {i}",
            status=IssueStatus.OPEN,
            last_synced_at=None,
        )
        db_session.add(issue)
        issues.append(issue)
    db_session.commit()

    # Mock synchronizer to fail on second issue
    mock_sync = Mock(spec=BaseIssueSynchronizer)
    mock_sync.can_sync.return_value = True

    def side_effect(issue: Issue) -> SyncResult:
        if issue.key == "1":
            return SyncResult(success=False, error="API Error")
        return SyncResult(success=True, new_title="Updated Title")

    mock_sync.fetch_issue_update.side_effect = side_effect

    # Create service and sync batch
    service = IssueSynchronizationService([mock_sync])
    results = service.sync_issues_batch(issues)

    # Verify results
    assert results.total == 3
    assert results.successful == 2
    assert results.updated == 2
    assert results.failed == 1
