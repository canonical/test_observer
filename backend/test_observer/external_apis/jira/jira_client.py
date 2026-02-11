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

import requests
from requests.auth import HTTPBasicAuth
from test_observer.external_apis.models import IssueData
import logging

logger = logging.getLogger(__name__)


class JiraClient:
    """Client for interacting with Jira API using scoped service account tokens"""

    def __init__(
        self,
        cloud_id: str,
        email: str,
        api_token: str,
        timeout: int = 30,
    ):
        """Initialize Jira client with scoped service account authentication

        Args:
            cloud_id: Jira cloud ID (e.g., "52d4faaa-fad4-4272-94e2-c183ca4c52b3")
            email: Email address for the service account
            api_token: Scoped API token (starts with ATATT...)
            timeout: Request timeout in seconds
        """
        self.base_url = f"https://api.atlassian.com/ex/jira/{cloud_id}"
        self.email = email
        self.api_token = api_token
        self.timeout = timeout

        logger.info(f"Initialized Jira client for cloud ID {cloud_id}")

    def get_issue(self, project: str, key: str) -> IssueData:  # noqa: ARG002
        """Get issue from Jira

        Args:
            project: Jira project key (e.g., "TO")
            key: Issue key (e.g., "TO-169")

        Returns:
            IssueData with title, status, and raw issue data

        Raises:
            Exception: If issue fetch fails
        """

        if "-" in key:
            issue_key = key
        elif project:
            issue_key = f"{project}-{key}"
        else:
            issue_key = key

        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"

        try:
            response = requests.get(
                url,
                auth=HTTPBasicAuth(self.email, self.api_token),
                headers={"Accept": "application/json"},
                timeout=self.timeout,
            )

            response.raise_for_status()
            data = response.json()

            fields = data.get("fields", {})
            status = fields.get("status", {}).get("name", "Unknown")

            return IssueData(
                title=fields.get("summary", ""),
                state=status,
                state_reason=None,
                raw=data,
            )

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching Jira issue {issue_key}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch Jira issue {issue_key}: {e}")
            raise
