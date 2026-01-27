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


from test_observer.external_apis.launchpad.launchpad_client import LaunchpadClient
from test_observer.external_apis.synchronizers.base import (
    BaseIssueSynchronizer,
    SyncResult,
)
from test_observer.data_access.models import Issue, IssueStatus
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class LaunchpadIssueSynchronizer(BaseIssueSynchronizer):
    """Synchronizer for Launchpad bugs"""

    def __init__(self, client: LaunchpadClient):
        self.client = client

    def can_sync(self, issue: Issue) -> bool:
        """Check if this issue is from Launchpad"""
        return issue.url is not None and "launchpad.net" in issue.url

    def sync_issue(self, issue: Issue, db: Session) -> SyncResult:
        """Synchronize a Launchpad bug"""
        try:
            # Fetch bug from Launchpad - use get_issue() for consistency
            issue_data = self.client.get_issue(issue.project, issue.key)

            # Track what changed
            title_updated = False
            status_updated = False

            # Update title if different
            if issue_data.title != issue.title:
                issue.title = issue_data.title
                title_updated = True
                logger.info(f"Updated title for issue {issue.id}: {issue_data.title}")

            # Map Launchpad status to IssueStatus
            new_status = self._map_launchpad_status(issue_data.state)
            if new_status != issue.status:
                issue.status = new_status
                status_updated = True
                logger.info(f"Updated status for issue {issue.id}: {new_status}")

            # Commit changes if any
            if title_updated or status_updated:
                db.commit()
                db.refresh(issue)

            return SyncResult(
                success=True, title_updated=title_updated, status_updated=status_updated
            )

        except Exception as e:
            logger.error(
                f"Failed to sync Launchpad bug {issue.id} from {issue.url}: {e}"
            )
            return SyncResult(success=False, error=str(e))

    @staticmethod
    def _map_launchpad_status(status: str) -> IssueStatus:
        """Map Launchpad bug status to IssueStatus enum

        In our system:
        - Fix Committed/Fix Released → CLOSED
        - Everything else (including In Progress, Incomplete) → OPEN
        """
        status_lower = status.lower()

        if status_lower in ["fix committed", "fix released", "closed"]:
            return IssueStatus.CLOSED
        else:
            # In progress, incomplete, new, etc. are all considered OPEN
            return IssueStatus.OPEN
