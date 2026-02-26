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

from github import Github, GithubIntegration, Auth
from test_observer.external_apis.models import IssueData
import logging
from typing import Any, cast

logger = logging.getLogger(__name__)


class GitHubClient:
    """Client for interacting with GitHub API using GitHub App authentication"""

    def __init__(self, app_id: str, private_key: str, timeout: int = 30):
        """Initialize GitHub client with App authentication

        Args:
            app_id: GitHub App ID
            private_key: GitHub App private key (PEM format)
            timeout: Request timeout in seconds
        """
        integration = GithubIntegration(app_id, private_key)

        # GitHub App installations represent the app being installed on specific
        # GitHub accounts or organizations. Each installation has its own access token.

        installations = list(integration.get_installations())

        if not installations:
            raise ValueError("No GitHub App installations found")

        # GitHub App is only installed once on the organization account, so any
        # installation will work. If multiple installations exist,
        # they all have the same permissions.

        installation = installations[0]

        auth = integration.get_access_token(installation.id)

        self._github = Github(auth=Auth.Token(auth.token), timeout=timeout)

    def get_issue(self, project: str, key: str) -> IssueData:
        """Get issue from GitHub

        Args:
            project: Repository in format "owner/repo"
            key: Issue number as string

        Returns:
            IssueData with title, state, labels, and raw GitHub issue object

        Raises:
            ValueError: If project format is invalid
            Exception: If issue fetch fails
        """

        if "/" not in project:
            raise ValueError(
                f"Invalid project format: {project}. Expected 'owner/repo'"
            )

        try:
            # Parse issue number
            issue_number = int(key)

            # Get repository and issue
            repo = self._github.get_repo(project)
            gh_issue = repo.get_issue(issue_number)

            # Extract labels from the GitHub issue
            labels = [label.name for label in gh_issue.labels]

            return IssueData(
                title=gh_issue.title,
                state=gh_issue.state,
                state_reason=gh_issue.state_reason,
                labels=labels,
                raw=cast(dict[str, Any], gh_issue.raw_data),
            )

        except Exception as e:
            logger.error(f"Failed to fetch GitHub issue {project}#{key}: {e}")
            raise
