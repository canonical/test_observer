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

import logging
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from test_observer.data_access.models import Issue, IssueStatus
from test_observer.external_apis.synchronizers.config import SyncConfig

logger = logging.getLogger(__name__)


class SyncStrategy:
    """Determines which issues need syncing based on priority and last sync time"""

    @classmethod
    def get_issues_due_for_sync(cls, db: Session, batch_size: int = 50, priority: str = "high") -> Sequence[Issue]:
        """
        Get issues that need syncing based on priority

        Args:
            db: Database session
            batch_size: Number of issues to return
            priority: 'high' (open), 'medium' (recent closed), 'low' (old closed)

        Returns:
            List of issues that need syncing
        """
        now = datetime.now(UTC)

        if priority == "high":
            # Open and unknown issues - unknown indicates newly created issues
            threshold = now - timedelta(seconds=SyncConfig.OPEN_ISSUE_INTERVAL)
            query = db.query(Issue).filter(
                Issue.status.in_([IssueStatus.OPEN, IssueStatus.UNKNOWN]),
                or_(Issue.last_synced_at.is_(None), Issue.last_synced_at < threshold),
            )

        elif priority == "medium":
            # Recently closed issues (< 30 days) not synced in last 6 hours
            closed_threshold = now - timedelta(days=SyncConfig.OLD_CLOSED_THRESHOLD_DAYS)
            sync_threshold = now - timedelta(seconds=SyncConfig.RECENT_CLOSED_INTERVAL)
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
            closed_threshold = now - timedelta(days=SyncConfig.OLD_CLOSED_THRESHOLD_DAYS)
            sync_threshold = now - timedelta(seconds=SyncConfig.OLD_CLOSED_INTERVAL)
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
        issues = query.order_by(Issue.last_synced_at.asc().nullsfirst()).limit(batch_size).all()

        logger.info(f"Found {len(issues)} {priority} priority issues due for sync")
        return issues

    @classmethod
    def get_sync_stats(cls, db: Session) -> dict:
        """Get statistics about sync status"""
        now = datetime.now(UTC)

        # Count open and unknown issues
        open_count = db.query(Issue).filter(Issue.status.in_([IssueStatus.OPEN, IssueStatus.UNKNOWN])).count()

        # Count recently closed issues
        recent_closed_threshold = now - timedelta(days=SyncConfig.OLD_CLOSED_THRESHOLD_DAYS)
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
