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

from test_observer.external_apis.github import GitHubClient
from test_observer.external_apis.synchronizers.base import (
    BaseIssueSynchronizer,
    SyncResult,
)
from test_observer.data_access.models import Issue, IssueStatus
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class GitHubIssueSynchronizer(BaseIssueSynchronizer):
    """Synchronizer for GitHub issues"""

    def __init__(self, client: GitHubClient):
        self.client = client

    def can_sync(self, issue: Issue) -> bool:
        """Check if this issue is from GitHub"""
        return issue.url is not None and "github.com" in issue.url

    def sync_issue(self, issue: Issue, db: Session) -> SyncResult:
        """Synchronize a GitHub issue"""
        try:
            # Fetch issue from GitHub
            gh_issue = self.client.get_issue(issue.project, issue.key)

            # Track what changed
            title_updated = False
            status_updated = False

            # Update title if different
            if gh_issue.title != issue.title:
                issue.title = gh_issue.title
                title_updated = True
                logger.info(f"Updated title for issue {issue.id}: {gh_issue.title}")

            # Map GitHub state to IssueStatus
            new_status = self._map_github_state(gh_issue.state)
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
                f"Failed to sync GitHub issue {issue.id} from {issue.url}: {e}"
            )
            return SyncResult(success=False, error=str(e))

    @staticmethod
    def _map_github_state(state: str) -> IssueStatus:
        """Map GitHub issue state to IssueStatus enum"""
        state_mapping = {
            "open": IssueStatus.OPEN,
            "closed": IssueStatus.CLOSED,
        }
        return state_mapping.get(state.lower(), IssueStatus.OPEN)
