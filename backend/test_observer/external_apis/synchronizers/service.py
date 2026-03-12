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

from test_observer.data_access.models import Issue
from test_observer.external_apis.synchronizers.base import (
    BaseIssueSynchronizer,
    SyncResult,
)
from test_observer.external_apis.synchronizers.models import SyncResults

logger = logging.getLogger(__name__)


class IssueSynchronizationService:
    """Orchestrates synchronization across multiple platforms"""

    def __init__(self, synchronizers: Sequence[BaseIssueSynchronizer]):
        """
        Initialize service with platform synchronizers

        Args:
            synchronizers: Sequence of platform-specific synchronizers
        """
        if not synchronizers:
            raise ValueError("At least one synchronizer is required")

        self.synchronizers = synchronizers
        logger.info(f"Initialized service with {len(synchronizers)} synchronizers")

    def sync_issue(self, issue: Issue) -> SyncResult:
        """
        Find appropriate synchronizer and fetch the latest state via HTTP.
        Does not write to the database.

        Args:
            issue: Issue to synchronize

        Returns:
            SyncResult with synchronization outcome
        """
        for synchronizer in self.synchronizers:
            if synchronizer.can_sync(issue):
                logger.debug(f"Using {synchronizer.__class__.__name__} for issue {issue.id}")
                return synchronizer.fetch_issue_update(issue)

        logger.warning(f"No synchronizer available for issue {issue.id} with URL: {issue.url}")
        return SyncResult(success=False, error=f"No synchronizer available for URL: {issue.url}")

    def sync_issues_batch(self, issues: Sequence[Issue]) -> SyncResults:
        """
        Fetch updates for a batch of issues via HTTP. Does not write to the database.

        Args:
            issues: List of issues to sync

        Returns:
            SyncResults with aggregated results
        """
        logger.info(f"Starting synchronization of {len(issues)} issues in batch")

        results = [self.sync_issue(issue) for issue in issues]

        sync_results = SyncResults.from_results(results)
        logger.info(
            f"Batch complete: "
            f"{sync_results.successful}/{sync_results.total} successful, "
            f"{sync_results.updated} updated, {sync_results.failed} failed"
        )

        return sync_results
