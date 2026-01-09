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

from __future__ import annotations

from jira import JIRA
from jira.exceptions import JIRAError

from test_observer.external_apis.exceptions import (
    IssueNotFoundError,
    APIError,
    RateLimitError,
)

from test_observer.external_apis.models import IssueData


class JiraClient:
    """Jira issue client using python-jira library"""

    def __init__(
        self,
        base_url: str,
        *,
        email: str | None = None,
        api_token: str | None = None,
        bearer_token: str | None = None,
        timeout: int = 10,
    ):
        """
        Args:
            base_url: Jira instance URL (e.g., https://your-domain.atlassian.net)
            email: Email for Cloud authentication
            api_token: API token for Cloud authentication
            bearer_token: Bearer token for DC/Server authentication
            timeout: request timeout (seconds)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Build auth tuple/token
        auth: tuple[str, str] | str | None = None
        if bearer_token:
            auth = bearer_token
        elif email and api_token:
            auth = (email, api_token)

        # Initialize Jira client
        self._jira = JIRA(
            server=self.base_url,
            basic_auth=auth if isinstance(auth, tuple) else None,
            token_auth=auth if isinstance(auth, str) else None,
            timeout=timeout,
        )

    def get_issue(self, project: str, key: str) -> IssueData:
        """
        Fetch an issue from Jira.

        Args:
            project: Project key (e.g., "TO")
            key: Issue key/number (e.g., "142" or "TO-142")

        Returns:
            IssueData object
        Raises:
            IssueNotFoundError: Issue not found
            RateLimitError: Rate limit exceeded
            APIError: Other API errors
        """
        try:
            # Normalize issue key
            issue_key = self._normalize_issue_key(project, key)

            # Fetch issue
            issue = self._jira.issue(issue_key)
            resolution = (
                issue.fields.resolution.name if issue.fields.resolution else None
            )
            # Normalize status
            state = self._normalize_state(
                status_category=(
                    issue.fields.status.statusCategory.key
                    if issue.fields.status.statusCategory
                    else None
                ),
                resolution=resolution,
            )
            return IssueData(
                title=issue.fields.summary,
                state=state,
                state_reason=issue.fields.status.name,
                raw={
                    "key": issue.key,
                    "summary": issue.fields.summary,
                    "status": issue.fields.status.name,
                    "resolution": resolution,
                    "url": issue.permalink(),
                },
            )
        except JIRAError as e:
            if e.status_code == 404:
                raise IssueNotFoundError(f"Jira issue {project}/{key} not found") from e
            if e.status_code == 429:
                raise RateLimitError(f"Jira rate limit exceeded: {e}") from e
            if e.status_code == 401:
                raise APIError("Jira authentication failed. Check credentials.") from e
            if e.status_code == 403:
                raise APIError("Jira permission denied. Check user permissions.") from e
            raise APIError(f"Jira API error: {e}") from e
        except Exception as e:
            raise APIError(f"Failed to fetch Jira issue: {e}") from e

    def _normalize_issue_key(self, project: str, key: str) -> str:
        """Normalize issue key to format PROJECT-123"""
        k = str(key).strip().upper()
        if k.startswith("#"):
            k = k[1:]
        if "-" not in k and project:
            return f"{project.strip().upper()}-{k}"
        return k

    def _normalize_state(
        self, status_category: str | None = None, resolution: str | None = None
    ) -> str:
        """Map Jira status to simple open/closed format"""
        if status_category == "done":
            return "closed"
        if resolution:
            return "closed"
        return "open"
