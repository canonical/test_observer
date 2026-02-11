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

from test_observer.external_apis.synchronizers.base import BaseIssueSynchronizer
from test_observer.external_apis.jira.jira_client import JiraClient
from test_observer.data_access.models import Issue, IssueStatus


class JiraIssueSynchronizer(BaseIssueSynchronizer):
    """Synchronizer for Jira issues"""

    def __init__(self, client: JiraClient):
        """Initialize with Jira client

        Args:
            client: JiraClient instance for API access
        """
        super().__init__(client)

    def can_sync(self, issue: Issue) -> bool:
        """Check if this issue is from Jira"""
        return issue.url is not None and (
            "atlassian.net" in issue.url or "jira" in issue.url.lower()
        )

    @staticmethod
    def _map_issue_status(state: str) -> IssueStatus:
        """Map Jira status to IssueStatus enum"""
        if state.lower() in ["done", "closed", "resolved"]:
            return IssueStatus.CLOSED
        else:
            # In progress, in review, to do, etc. are all considered OPEN
            return IssueStatus.OPEN
