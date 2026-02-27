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

from datetime import UTC, datetime
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


def test_sync_issue_updates_last_synced_at(db_session: Session) -> None:
    """Test that successful sync updates last_synced_at"""
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

    assert issue.last_synced_at is None

    # Mock synchronizer
    mock_sync = Mock(spec=BaseIssueSynchronizer)
    mock_sync.can_sync.return_value = True
    mock_sync.sync_issue.return_value = SyncResult(success=True)

    # Create service and sync
    service = IssueSynchronizationService([mock_sync])
    before_sync = datetime.now(UTC)
    result = service.sync_issue(issue, db_session)
    after_sync = datetime.now(UTC)

    # Verify last_synced_at was updated
    assert result.success is True
    assert issue.last_synced_at is not None

    synced_at = (
        issue.last_synced_at.replace(tzinfo=UTC) if issue.last_synced_at.tzinfo is None else issue.last_synced_at
    )
    assert before_sync <= synced_at <= after_sync


def test_sync_issue_does_not_update_on_failure(db_session: Session) -> None:
    """Test that failed sync does NOT update last_synced_at"""
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
    mock_sync.sync_issue.return_value = SyncResult(success=False, error="API Error")

    # Create service and sync
    service = IssueSynchronizationService([mock_sync])
    result = service.sync_issue(issue, db_session)

    # Verify last_synced_at was NOT updated
    assert result.success is False
    assert issue.last_synced_at is None


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
    mock_sync.sync_issue.return_value = SyncResult(success=True, title_updated=True)

    # Create service and sync batch
    service = IssueSynchronizationService([mock_sync])
    results = service.sync_issues_batch(issues, db_session)

    # Verify results
    assert results.total == 5
    assert results.successful == 5
    assert results.updated == 5
    assert results.failed == 0

    # Verify all issues have last_synced_at set
    for issue in issues:
        db_session.refresh(issue)
        assert issue.last_synced_at is not None


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

    def side_effect(issue: Issue, _db: Session) -> SyncResult:
        if issue.key == "1":
            return SyncResult(success=False, error="API Error")
        return SyncResult(success=True, title_updated=True)

    mock_sync.sync_issue.side_effect = side_effect

    # Create service and sync batch
    service = IssueSynchronizationService([mock_sync])
    results = service.sync_issues_batch(issues, db_session)

    # Verify results
    assert results.total == 3
    assert results.successful == 2
    assert results.updated == 2
    assert results.failed == 1

    # Verify only successful issues have last_synced_at set
    db_session.refresh(issues[0])
    db_session.refresh(issues[1])
    db_session.refresh(issues[2])

    assert issues[0].last_synced_at is not None  # Success
    assert issues[1].last_synced_at is None  # Failed
    assert issues[2].last_synced_at is not None  # Success
