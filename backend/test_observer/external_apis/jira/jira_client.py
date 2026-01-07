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
import base64
import requests

from test_observer.external_apis.exceptions import (
    IssueNotFoundError,
    APIError,
    RateLimitError,
)


class JiraClient:
    """
    Minimal Jira issue client with Cloud + DC compatibility.

    Auth modes:
      - Jira Cloud: email + api_token via Basic Auth (email:token)
      - Jira DC/Server: personal access token via Bearer
    """

    def __init__(
        self,
        base_url: str,
        *,
        # Cloud-style
        email: str | None = None,
        api_token: str | None = None,
        # DC-style
        bearer_token: str | None = None,
        # API version
        api_version: int = 3,
        timeout: int = 10,
    ):
        """
        Args:
            base_url: e.g. https://your-domain.atlassian.net
            email/api_token: Jira Cloud API token auth (Basic)
            bearer_token: Jira DC/Server PAT auth (Bearer)
            api_version: 3 for Cloud v3 endpoints; 2 for older Jira / DC setups.
            timeout: request timeout
        """
        self.base_url = base_url.rstrip("/")
        self.api_version = api_version
        self.timeout = timeout

        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "test-observer-issue-sync/1.0",
                "Accept": "application/json",
            }
        )

        # Auth preference: Bearer > Basic (Cloud)
        if bearer_token:
            self._session.headers.update({"Authorization": f"Bearer {bearer_token}"})
        elif email and api_token:
            token_bytes = f"{email}:{api_token}".encode()
            b64 = base64.b64encode(token_bytes).decode("ascii")
            self._session.headers.update({"Authorization": f"Basic {b64}"})
        # else: anonymous/unauth (may work if Jira allows anonymous browsing; often not)

    def get_issue(self, project: str, key: str) -> dict[str, Any]:
        """
        Fetch an issue from Jira.

        Args:
            project: project key like "TO" or "SQT"
            key: issue key like "TO-123". If user passes "123",
            we'll turn it into "{project}-123" if project is given.

        Returns:
            dict with keys 'title', 'state', 'raw' (API response)
        Raises:
            IssueNotFoundError: 404
            RateLimitError: 429
            APIError: others
        """
        issue_key = self._normalize_issue_key(project, key)
        url = f"{self.base_url}/rest/api/{self.api_version}/issue/{issue_key}"

        params = {
            "fields": "summary,status,resolution,resolutiondate,updated,created,issuetype,project",
        }

        try:
            resp = self._session.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as e:
            raise APIError(f"Jira request failed: {e}") from e

        if resp.status_code == 404:
            raise IssueNotFoundError(f"Jira issue {issue_key} not found")

        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            reset = resp.headers.get("X-RateLimit-Reset")
            msg = "Jira rate limit exceeded (429)."
            if retry_after:
                msg += f" Retry after {retry_after}s."
            if reset:
                msg += f" Reset at {reset}."
            raise RateLimitError(msg)

        if resp.status_code == 401:
            raise APIError("Jira authentication failed (401). Check credentials/token.")
        if resp.status_code == 403:
            raise APIError(
                "Jira permission denied (403). "
                "User/token may lack Browse permission for this project."
            )

        if not resp.ok:
            raise APIError(f"Jira API returned {resp.status_code}: {resp.text}")

        data = resp.json() if resp.text else {}
        fields = data.get("fields", {}) or {}

        summary = (fields.get("summary") or "").strip()
        status_obj = fields.get("status") or {}
        status_name = status_obj.get("name")  # e.g. "To Do", "In Progress", "Done"
        status_category = (status_obj.get("statusCategory") or {}).get(
            "key"
        )  # e.g. "done"
        resolution = (fields.get("resolution") or {}).get("name")

        state = self._normalize_state(
            status_category=status_category, resolution=resolution
        )

        return {
            "title": summary,
            "state": state,
            "state_reason": status_name,
            "raw": data,
        }

    def _normalize_issue_key(self, project: str, key: str) -> str:
        k = str(key).strip().upper()
        if k.startswith("#"):
            k = k[1:]
        if "/browse/" in k:
            k = k.split("/browse/")[-1]
        if "-" not in k and project:
            return f"{project.strip().upper()}-{k}"
        return k

    def _normalize_state(
        self, status_category: str | None = None, resolution: str | None = None
    ) -> str:
        if status_category == "done":
            return "closed"
        if resolution:
            return "closed"
        return "open"
