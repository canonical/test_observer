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


from test_observer.external_apis.synchronizers.base import (
    BaseIssueSynchronizer,
    SyncResult,
)
from test_observer.external_apis.synchronizers.models import SyncResults
from test_observer.data_access.models import Issue
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class IssueSynchronizationService:
    """Orchestrates synchronization across multiple platforms"""

    def __init__(self, synchronizers: list[BaseIssueSynchronizer]):
        """
        Initialize service with platform synchronizers

        Args:
            synchronizers: List of platform-specific synchronizers
        """
        if not synchronizers:
            raise ValueError("At least one synchronizer is required")

        self.synchronizers = synchronizers
        logger.info(f"Initialized service with {len(synchronizers)} synchronizers")

    def sync_issue(self, issue: Issue, db: Session) -> SyncResult:
        """
        Find appropriate synchronizer and sync the issue

        Args:
            issue: Issue to synchronize
            db: Database session

        Returns:
            SyncResult with synchronization outcome
        """
        for synchronizer in self.synchronizers:
            if synchronizer.can_sync(issue):
                logger.debug(
                    f"Using {synchronizer.__class__.__name__} for issue {issue.id}"
                )
                return synchronizer.sync_issue(issue, db)

        logger.warning(
            f"No synchronizer available for issue {issue.id} with URL: {issue.url}"
        )
        return SyncResult(
            success=False, error=f"No synchronizer available for URL: {issue.url}"
        )

    def sync_all_issues(self, db: Session) -> SyncResults:
        """
        Sync all issues in the database

        Args:
            db: Database session

        Returns:
            SyncResults with aggregated results
        """
        issues = db.query(Issue).all()
        logger.info(f"Starting synchronization of {len(issues)} issues")

        results = [self.sync_issue(issue, db) for issue in issues]

        sync_results = SyncResults.from_results(results)
        logger.info(
            f"Synchronization complete: "
            f"{sync_results.successful}/{sync_results.total} successful, "
            f"{sync_results.updated} updated, {sync_results.failed} failed"
        )

        return sync_results
