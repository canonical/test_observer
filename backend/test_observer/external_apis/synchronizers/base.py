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

from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from test_observer.data_access.models import Issue, IssueStatus
from test_observer.external_apis.github import GitHubClient
from test_observer.external_apis.jira import JiraClient
from test_observer.external_apis.launchpad import LaunchpadClient
import logging

logger = logging.getLogger(__name__)


class SyncResult:
    """Result of a synchronization operation"""

    def __init__(
        self,
        success: bool,
        title_updated: bool = False,
        status_updated: bool = False,
        labels_updated: bool = False,
        error: str | None = None,
    ):
        self.success = success
        self.title_updated = title_updated
        self.status_updated = status_updated
        self.labels_updated = labels_updated
        self.error = error


class BaseIssueSynchronizer(ABC):
    """Base class for issue synchronizers"""

    def __init__(self, client: GitHubClient | JiraClient | LaunchpadClient):
        """Initialize with API client"""
        self.client = client

    @abstractmethod
    def can_sync(self, issue: Issue) -> bool:
        """Check if this synchronizer can handle the given issue"""
        pass

    def sync_issue(self, issue: Issue, db: Session) -> SyncResult:
        """Synchronize an issue from the client service"""
        try:
            # Fetch issue from external service
            client_issue = self.client.get_issue(issue.project, issue.key)

            title_updated = False
            status_updated = False
            labels_updated = False

            if client_issue.title != issue.title:
                issue.title = client_issue.title
                title_updated = True
                logger.info(f"Updated title for issue {issue.id}: {client_issue.title}")

            new_status = self._map_issue_status(client_issue.state)
            if new_status != issue.status:
                issue.status = new_status
                status_updated = True
                logger.info(f"Updated status for issue {issue.id}: {new_status}")

            new_labels = sorted(client_issue.labels)
            current_labels = sorted(issue.labels or [])
            if new_labels != current_labels:
                issue.labels = new_labels
                labels_updated = True
                logger.info(f"Updated labels for issue {issue.id}: {new_labels}")

            if title_updated or status_updated or labels_updated:
                db.commit()
                db.refresh(issue)

            return SyncResult(
                success=True,
                title_updated=title_updated,
                status_updated=status_updated,
                labels_updated=labels_updated,
            )

        except Exception as e:
            logger.error(f"Failed to sync issue {issue.id} from {issue.url}: {e}")
            return SyncResult(success=False, error=str(e))

    @staticmethod
    @abstractmethod
    def _map_issue_status(state: str) -> IssueStatus:
        """Map the provided status to an IssueStatus enum"""
        pass
