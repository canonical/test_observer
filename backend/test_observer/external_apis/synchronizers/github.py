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

from test_observer.data_access.models import Issue, IssueStatus
from test_observer.external_apis.github.github_client import GitHubClient
from test_observer.external_apis.synchronizers.base import BaseIssueSynchronizer


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
