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

from github import Github, Auth, GithubException

from test_observer.external_apis.exceptions import (
    IssueNotFoundError,
    APIError,
    RateLimitError,
)

from test_observer.external_apis.models import IssueData


class GitHubClient:
    """GitHub issue client using PyGithub"""

    def __init__(self, token: str | None = None, timeout: int = 10):
        """
        Args:
            token: Personal Access Token (classic PAT or fine-grained token)
            timeout: request timeout (seconds)
        """
        self.token = token
        self.timeout = timeout

        # Initialize Github client with proper auth
        auth = Auth.Token(token) if token else None
        self._github = Github(auth=auth, timeout=timeout)

    def get_issue(self, project: str, key: str) -> IssueData:
        """
        Fetch an issue from GitHub.

        Args:
            project: "owner/repo" format
            key: issue number (string/int)

        Returns:
            dict with keys 'title', 'state', 'state_reason', 'raw'
        Raises:
            IssueNotFoundError: Issue not found
            RateLimitError: Rate limit exceeded
            APIError: Other API errors
        """
        try:
            repo = self._github.get_repo(project)
            issue = repo.get_issue(int(str(key).lstrip("#")))

            return {
                "title": issue.title,
                "state": issue.state,
                "state_reason": issue.state_reason,
                "raw": {
                    "id": issue.id,
                    "number": issue.number,
                    "title": issue.title,
                    "state": issue.state,
                    "state_reason": issue.state_reason,
                    "url": issue.html_url,
                },
            }
        except GithubException as e:
            if e.status == 404:
                raise IssueNotFoundError(
                    f"GitHub issue {project}#{key} not found"
                ) from e
            if e.status == 403 and "API rate limit" in str(e):
                raise RateLimitError(f"GitHub rate limit exceeded: {e}") from e
            if e.status == 401:
                raise APIError("GitHub authentication failed. Check token.") from e
            raise APIError(f"GitHub API error: {e}") from e
        except Exception as e:
            raise APIError(f"Failed to fetch GitHub issue: {e}") from e
