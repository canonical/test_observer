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

from datetime import datetime, timedelta
from collections.abc import Sequence
from sqlalchemy import or_
from sqlalchemy.orm import Session

from test_observer.data_access.models import Issue, IssueStatus
import logging

logger = logging.getLogger(__name__)


class SyncStrategy:
    """Determines which issues need syncing based on priority and last sync time"""

    # Sync intervals in seconds
    OPEN_ISSUE_INTERVAL = 3600  # 1 hour
    RECENT_CLOSED_INTERVAL = 21600  # 6 hours
    OLD_CLOSED_INTERVAL = 604800  # 7 days

    # Age threshold for "old" closed issues (30 days)
    OLD_CLOSED_THRESHOLD_DAYS = 30

    @classmethod
    def get_issues_due_for_sync(
        cls, db: Session, batch_size: int = 50, priority: str = "high"
    ) -> Sequence[Issue]:
        """
        Get issues that need syncing based on priority

        Args:
            db: Database session
            batch_size: Number of issues to return
            priority: 'high' (open), 'medium' (recent closed), 'low' (old closed)

        Returns:
            List of issues that need syncing
        """
        now = datetime.utcnow()

        if priority == "high":
            # Open issues not synced in the last hour
            threshold = now - timedelta(seconds=cls.OPEN_ISSUE_INTERVAL)
            query = db.query(Issue).filter(
                Issue.status == IssueStatus.OPEN,
                or_(Issue.last_synced_at.is_(None), Issue.last_synced_at < threshold),
            )

        elif priority == "medium":
            # Recently closed issues (< 30 days) not synced in last 6 hours
            closed_threshold = now - timedelta(days=cls.OLD_CLOSED_THRESHOLD_DAYS)
            sync_threshold = now - timedelta(seconds=cls.RECENT_CLOSED_INTERVAL)
            query = db.query(Issue).filter(
                Issue.status == IssueStatus.CLOSED,
                Issue.updated_at >= closed_threshold,
                or_(
                    Issue.last_synced_at.is_(None),
                    Issue.last_synced_at < sync_threshold,
                ),
            )

        elif priority == "low":
            # Old closed issues (> 30 days) not synced in last 7 days
            closed_threshold = now - timedelta(days=cls.OLD_CLOSED_THRESHOLD_DAYS)
            sync_threshold = now - timedelta(seconds=cls.OLD_CLOSED_INTERVAL)
            query = db.query(Issue).filter(
                Issue.status == IssueStatus.CLOSED,
                Issue.updated_at < closed_threshold,
                or_(
                    Issue.last_synced_at.is_(None),
                    Issue.last_synced_at < sync_threshold,
                ),
            )

        else:
            raise ValueError(f"Invalid priority: {priority}")

        # Order by oldest sync first, limit to batch size
        issues = (
            query.order_by(Issue.last_synced_at.asc().nullsfirst())
            .limit(batch_size)
            .all()
        )

        logger.info(f"Found {len(issues)} {priority} priority issues due for sync")
        return issues

    @classmethod
    def get_sync_stats(cls, db: Session) -> dict:
        """Get statistics about sync status"""
        now = datetime.utcnow()

        # Count open issues
        open_count = db.query(Issue).filter(Issue.status == IssueStatus.OPEN).count()

        # Count recently closed issues
        recent_closed_threshold = now - timedelta(days=cls.OLD_CLOSED_THRESHOLD_DAYS)
        recent_closed_count = (
            db.query(Issue)
            .filter(
                Issue.status == IssueStatus.CLOSED,
                Issue.updated_at >= recent_closed_threshold,
            )
            .count()
        )

        # Count old closed issues
        old_closed_count = (
            db.query(Issue)
            .filter(
                Issue.status == IssueStatus.CLOSED,
                Issue.updated_at < recent_closed_threshold,
            )
            .count()
        )

        # Count never synced
        never_synced = db.query(Issue).filter(Issue.last_synced_at.is_(None)).count()

        return {
            "open_issues": open_count,
            "recent_closed_issues": recent_closed_count,
            "old_closed_issues": old_closed_count,
            "never_synced": never_synced,
            "total": open_count + recent_closed_count + old_closed_count,
        }
