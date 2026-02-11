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
from test_observer.external_apis.github.github_client import GitHubClient
from test_observer.data_access.models import Issue, IssueStatus


class GitHubIssueSynchronizer(BaseIssueSynchronizer):
    """Synchronizer for GitHub issues"""

    def __init__(self, client: GitHubClient):
        """Initialize with GitHub client

        Args:
            client: GitHubClient instance for API access
        """
        super().__init__(client)

    def can_sync(self, issue: Issue) -> bool:
        """Check if this issue is from GitHub"""
        return issue.url is not None and "github.com" in issue.url

    @staticmethod
    def _map_issue_status(state: str) -> IssueStatus:
        """Map GitHub issue state to IssueStatus enum"""
        state_mapping = {
            "open": IssueStatus.OPEN,
            "closed": IssueStatus.CLOSED,
        }
        return state_mapping.get(state.lower(), IssueStatus.OPEN)
