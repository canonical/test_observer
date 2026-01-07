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
from typing import Any

import requests

from test_observer.external_apis.exceptions import (
    IssueNotFoundError,
    APIError,
    RateLimitError,
)


class GitHubClient:
    def __init__(
        self, token: str | None = None, base_url: str | None = None, timeout: int = 10
    ):
        """
        Args:
            token: Personal Access Token (classic PAT or fine-grained token)
            base_url: GitHub API base (default: https://api.github.com).
            timeout: request timeout
        """
        self.token = token
        self.base_url = base_url.rstrip("/") if base_url else "https://api.github.com"
        self.timeout = timeout
        self._session = requests.Session()
        if self.token:
            self._session.headers.update({"Authorization": f"Bearer {self.token}"})
        self._session.headers.update(
            {
                "User-Agent": "test-observer-issue-sync/1.0",
                "Accept": "application/vnd.github+json",
            }
        )

    def get_issue(self, project: str, key: str) -> dict[str, Any]:
        """
        Fetch an issue from GitHub.

        Args:
            project: "owner/repo" format
            key: issue number (string/int)

        Returns:
            dict with keys 'title', 'state', and 'raw' (API response)
        Raises:
            IssueNotFoundError: 404
            RateLimitError: when rate-limited
            APIError: other non-200 responses or request failures
        """
        owner_repo = project
        issue_number = str(key).lstrip("#")
        url = f"{self.base_url}/repos/{owner_repo}/issues/{issue_number}"

        try:
            resp = self._session.get(url, timeout=self.timeout)
        except requests.RequestException as e:
            raise APIError(f"GitHub request failed: {e}") from e

        # 404 -> not found / not visible to token
        if resp.status_code == 404:
            raise IssueNotFoundError(
                f"GitHub issue {owner_repo}#{issue_number} not found"
            )

        # Rate limiting
        if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
            reset = resp.headers.get("X-RateLimit-Reset")
            raise RateLimitError(f"GitHub rate limit exceeded; reset at {reset}")

        # Auth issues
        if resp.status_code == 401:
            raise APIError("GitHub authentication failed (401). Check token.")
        if (
            resp.status_code == 403
            and resp.headers.get("X-RateLimit-Remaining") is not None
        ):
            # permission denied likely
            raise APIError(
                "GitHub permission denied (403). Token may lack repo access."
            )

        if not resp.ok:
            raise APIError(f"GitHub API returned {resp.status_code}: {resp.text}")

        data = resp.json() if resp.text else {}
        return {
            "title": data.get("title", "") or "",
            "state": data.get("state"),
            "state_reason": data.get("state_reason"),
            "raw": data,
        }
