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

from test_observer.external_apis.synchronizers.base import BaseIssueSynchronizer
from test_observer.external_apis.launchpad.launchpad_client import LaunchpadClient
from test_observer.data_access.models import Issue, IssueStatus


class LaunchpadIssueSynchronizer(BaseIssueSynchronizer):
    """Synchronizer for Launchpad bugs"""

    def __init__(self, client: LaunchpadClient):
        """Initialize with Launchpad client

        Args:
            client: LaunchpadClient instance for API access
        """
        super().__init__(client)

    def can_sync(self, issue: Issue) -> bool:
        """Check if this issue is from Launchpad"""
        return issue.url is not None and "launchpad.net" in issue.url

    @staticmethod
    def _map_issue_status(state: str) -> IssueStatus:
        """Map Launchpad bug status to IssueStatus enum

        In our system:
        - Fix Committed/Fix Released → CLOSED
        - Everything else (including In Progress, Incomplete) → OPEN
        """
        if state.lower() in ["fix committed", "fix released", "closed"]:
            return IssueStatus.CLOSED
        else:
            # In progress, incomplete, new, etc. are all considered OPEN
            return IssueStatus.OPEN
