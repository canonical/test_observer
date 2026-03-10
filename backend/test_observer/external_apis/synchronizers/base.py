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
from abc import ABC, abstractmethod

from test_observer.data_access.models import Issue, IssueStatus
from test_observer.external_apis.github import GitHubClient
from test_observer.external_apis.jira import JiraClient
from test_observer.external_apis.launchpad import LaunchpadClient

logger = logging.getLogger(__name__)


class SyncResult:
    """Result of a synchronization operation"""

    def __init__(
        self,
        success: bool,
        error: str | None = None,
        new_title: str | None = None,
        new_status: IssueStatus | None = None,
        new_labels: list[str] | None = None,
    ):
        self.success = success
        self.error = error
        self.new_title = new_title
        self.new_status = new_status
        self.new_labels = new_labels

    @property
    def title_updated(self) -> bool:
        return self.new_title is not None

    @property
    def status_updated(self) -> bool:
        return self.new_status is not None

    @property
    def labels_updated(self) -> bool:
        return self.new_labels is not None


class BaseIssueSynchronizer(ABC):
    """Base class for issue synchronizers"""

    def __init__(self, client: GitHubClient | JiraClient | LaunchpadClient):
        """Initialize with API client"""
        self.client = client

    @abstractmethod
    def can_sync(self, issue: Issue) -> bool:
        """Check if this synchronizer can handle the given issue"""
        pass

    def fetch_issue_update(self, issue: Issue) -> SyncResult:
        """Fetch latest state from the external service. Does not access the database."""
        try:
            client_issue = self.client.get_issue(issue.project, issue.key)

            new_title = client_issue.title if client_issue.title != issue.title else None
            if new_title is not None:
                logger.info(f"Detected title change for issue {issue.id}: {new_title}")

            mapped_status = self._map_issue_status(client_issue.state)
            new_status = mapped_status if mapped_status != issue.status else None
            if new_status is not None:
                logger.info(f"Detected status change for issue {issue.id}: {new_status}")

            sorted_labels = sorted(client_issue.labels)
            new_labels = sorted_labels if sorted_labels != sorted(issue.labels or []) else None
            if new_labels is not None:
                logger.info(f"Detected label change for issue {issue.id}: {new_labels}")

            return SyncResult(
                success=True,
                new_title=new_title,
                new_status=new_status,
                new_labels=new_labels,
            )

        except Exception as e:
            logger.error(f"Failed to sync issue {issue.id} from {issue.url}: {e}")
            return SyncResult(success=False, error=str(e))

    @staticmethod
    @abstractmethod
    def _map_issue_status(state: str) -> IssueStatus:
        """Map the provided status to an IssueStatus enum"""
        pass
