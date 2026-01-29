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

from datetime import datetime, timedelta, UTC
import pytest
from sqlalchemy.orm import Session

from test_observer.external_apis.synchronizers.sync_strategy import SyncStrategy
from test_observer.data_access.models import Issue, IssueSource, IssueStatus


def test_get_open_issues_never_synced(db_session: Session) -> None:
    """Test that open issues that have never been synced are returned"""
    # Create open issue that has never been synced
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

    # Should be returned for high priority sync
    issues = SyncStrategy.get_issues_due_for_sync(
        db_session, batch_size=50, priority="high"
    )

    assert len(issues) == 1
    assert issues[0].id == issue.id


def test_get_open_issues_synced_recently(db_session: Session) -> None:
    """Test that recently synced open issues are NOT returned"""
    # Create open issue synced 30 minutes ago
    issue = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="123",
        title="Test Issue",
        status=IssueStatus.OPEN,
        last_synced_at=datetime.utcnow() - timedelta(minutes=30),
    )
    db_session.add(issue)
    db_session.commit()

    # Should NOT be returned (synced < 1 hour ago)
    issues = SyncStrategy.get_issues_due_for_sync(
        db_session, batch_size=50, priority="high"
    )

    assert len(issues) == 0


def test_get_open_issues_synced_long_ago(db_session: Session) -> None:
    """Test that open issues synced > 1 hour ago ARE returned"""
    # Create open issue synced 2 hours ago
    issue = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="123",
        title="Test Issue",
        status=IssueStatus.OPEN,
        last_synced_at=datetime.utcnow() - timedelta(hours=2),
    )
    db_session.add(issue)
    db_session.commit()

    # Should be returned (synced > 1 hour ago)
    issues = SyncStrategy.get_issues_due_for_sync(
        db_session, batch_size=50, priority="high"
    )

    assert len(issues) == 1
    assert issues[0].id == issue.id


def test_get_recent_closed_issues(db_session: Session) -> None:
    """Test that recently closed issues are returned for medium priority"""
    # Create closed issue from 10 days ago, never synced
    issue = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="123",
        title="Test Issue",
        status=IssueStatus.CLOSED,
        updated_at=datetime.utcnow() - timedelta(days=10),
        last_synced_at=None,
    )
    db_session.add(issue)
    db_session.commit()

    # Should be returned for medium priority sync
    issues = SyncStrategy.get_issues_due_for_sync(
        db_session, batch_size=50, priority="medium"
    )

    assert len(issues) == 1
    assert issues[0].id == issue.id


def test_old_closed_issues_not_in_medium_priority(db_session: Session) -> None:
    """Test that old closed issues are NOT in medium priority"""
    # Create closed issue from 40 days ago
    issue = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="123",
        title="Test Issue",
        status=IssueStatus.CLOSED,
        updated_at=datetime.utcnow() - timedelta(days=40),
        last_synced_at=None,
    )
    db_session.add(issue)
    db_session.commit()

    # Should NOT be in medium priority (too old)
    issues = SyncStrategy.get_issues_due_for_sync(
        db_session, batch_size=50, priority="medium"
    )

    assert len(issues) == 0


def test_get_old_closed_issues(db_session: Session) -> None:
    """Test that old closed issues are returned for low priority"""
    # Create closed issue from 40 days ago, never synced
    issue = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="123",
        title="Test Issue",
        status=IssueStatus.CLOSED,
        updated_at=datetime.utcnow() - timedelta(days=40),
        last_synced_at=None,
    )
    db_session.add(issue)
    db_session.commit()

    # Should be returned for low priority sync
    issues = SyncStrategy.get_issues_due_for_sync(
        db_session, batch_size=50, priority="low"
    )

    assert len(issues) == 1
    assert issues[0].id == issue.id


def test_batch_size_limit(db_session: Session) -> None:
    """Test that batch size is respected"""
    # Create 100 open issues
    for i in range(100):
        issue = Issue(
            source=IssueSource.GITHUB,
            project="canonical/test-repo",
            key=str(i),
            title=f"Test Issue {i}",
            status=IssueStatus.OPEN,
            last_synced_at=None,
        )
        db_session.add(issue)
    db_session.commit()

    # Request batch of 25
    issues = SyncStrategy.get_issues_due_for_sync(
        db_session, batch_size=25, priority="high"
    )

    assert len(issues) == 25


def test_oldest_sync_first(db_session: Session) -> None:
    """Test that issues are returned in order of oldest sync first"""
    # Create issues with different sync times
    issue1 = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="1",
        title="Test 1",
        status=IssueStatus.OPEN,
        last_synced_at=datetime.now(UTC) - timedelta(hours=5),
    )
    issue2 = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="2",
        title="Test 2",
        status=IssueStatus.OPEN,
        last_synced_at=datetime.now(UTC) - timedelta(hours=3),
    )
    issue3 = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="3",
        title="Test 3",
        status=IssueStatus.OPEN,
        last_synced_at=None,  # Never synced
    )
    db_session.add_all([issue1, issue2, issue3])
    db_session.commit()

    issues = SyncStrategy.get_issues_due_for_sync(
        db_session, batch_size=50, priority="high"
    )

    # Never synced should be first, then oldest
    assert len(issues) == 3
    assert issues[0].id == issue3.id  # Never synced
    assert issues[1].id == issue1.id  # Oldest sync
    assert issues[2].id == issue2.id  # Newer sync


def test_get_sync_stats(db_session: Session) -> None:
    """Test sync statistics calculation"""
    now = datetime.utcnow()

    # Create various issues
    open_issue = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="1",
        title="Open",
        status=IssueStatus.OPEN,
        updated_at=now,
        last_synced_at=now - timedelta(hours=1),
    )
    recent_closed = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="2",
        title="Recent Closed",
        status=IssueStatus.CLOSED,
        updated_at=now - timedelta(days=10),
        last_synced_at=now - timedelta(hours=2),
    )
    old_closed = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="3",
        title="Old Closed",
        status=IssueStatus.CLOSED,
        updated_at=now - timedelta(days=40),
        last_synced_at=now - timedelta(days=8),
    )
    never_synced = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="4",
        title="Never Synced",
        status=IssueStatus.OPEN,
        last_synced_at=None,
    )

    db_session.add_all([open_issue, recent_closed, old_closed, never_synced])
    db_session.commit()

    stats = SyncStrategy.get_sync_stats(db_session)

    assert stats["open_issues"] == 2
    assert stats["recent_closed_issues"] == 1
    assert stats["old_closed_issues"] == 1
    assert stats["never_synced"] == 1
    assert stats["total"] == 4


def test_invalid_priority_raises_error(db_session: Session) -> None:
    """Test that invalid priority raises ValueError"""
    with pytest.raises(ValueError, match="Invalid priority"):
        SyncStrategy.get_issues_due_for_sync(
            db_session, batch_size=50, priority="invalid"
        )


def test_closed_issue_respects_sync_interval(db_session: Session) -> None:
    """Test that recently synced closed issues are not returned"""
    # Create closed issue synced 3 hours ago (medium priority interval is 6 hours)
    issue = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="123",
        title="Test Issue",
        status=IssueStatus.CLOSED,
        updated_at=datetime.now(UTC) - timedelta(days=10),
        last_synced_at=datetime.now(UTC) - timedelta(hours=3),
    )
    db_session.add(issue)
    db_session.commit()

    # Should NOT be returned (synced < 6 hours ago)
    issues = SyncStrategy.get_issues_due_for_sync(
        db_session, batch_size=50, priority="medium"
    )

    assert len(issues) == 0

    # Create another issue synced 8 hours ago
    old_sync_issue = Issue(
        source=IssueSource.GITHUB,
        project="canonical/test-repo",
        key="456",
        title="Old Sync",
        status=IssueStatus.CLOSED,
        updated_at=datetime.now(UTC) - timedelta(days=10),
        last_synced_at=datetime.now(UTC) - timedelta(hours=8),
    )
    db_session.add(old_sync_issue)
    db_session.commit()

    # Should be returned (synced > 6 hours ago)
    issues = SyncStrategy.get_issues_due_for_sync(
        db_session, batch_size=50, priority="medium"
    )

    assert len(issues) == 1
    assert issues[0].id == old_sync_issue.id
