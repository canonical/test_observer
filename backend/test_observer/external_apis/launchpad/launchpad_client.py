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

from launchpadlib.launchpad import Launchpad  # type: ignore[import-untyped]
from lazr.restfulclient.errors import (  # type: ignore[import-untyped]
    NotFound,
    Unauthorized,
    HTTPError,
    ServerError,
)

from test_observer.external_apis.exceptions import (
    IssueNotFoundError,
    APIError,
)

from test_observer.external_apis.models import IssueData


class LaunchpadClient:
    """Launchpad bug client using launchpadlib"""

    def __init__(
        self,
        application_name: str = "test-observer-issue-sync",
        service_root: str = "production",
        version: str = "devel",
        timeout: int = 10,
        credentials_file: str | None = None,
        cache_dir: str | None = None,
        anonymous: bool = True,
    ):
        """
        Args:
            application_name: OAuth app name
            service_root: "production" or "staging"
            version: API version (usually "devel")
            timeout: HTTP timeout (seconds)
            credentials_file: Path to OAuth credentials file
            cache_dir: Optional cache directory
            anonymous: Use anonymous login if True
        """
        self.application_name = application_name
        self.service_root = service_root
        self.version = version
        self.timeout = timeout
        self.credentials_file = credentials_file
        self.cache_dir = cache_dir
        self.anonymous = anonymous if credentials_file is None else False

        self.launchpad = self._login()

    def _login(self) -> Launchpad:
        """Login to Launchpad"""
        try:
            if self.anonymous:
                return Launchpad.login_anonymously(
                    self.application_name,
                    self.service_root,
                    version=self.version,
                )

            if self.credentials_file:
                return Launchpad.login_with(
                    self.application_name,
                    self.service_root,
                    version=self.version,
                    credentials_file=self.credentials_file,
                )

            return Launchpad.login_with(
                self.application_name,
                self.service_root,
                version=self.version,
            )
        except Exception as e:
            raise APIError(f"Launchpad login failed: {e}") from e

    def get_issue(self, project: str, key: str) -> IssueData:
        """
        Fetch a Launchpad bug.

        Args:
            project: Project name (e.g., "ubuntu", "cloud-init")
            key: Bug ID (e.g., "1234567")

        Returns:
            IssueData object
        Raises:
            IssueNotFoundError: Bug not found
            APIError: Other API errors
        """
        try:
            bug_id = self._parse_bug_id(key)
            bug = self.launchpad.bugs[bug_id]

            # Get the most relevant task status
            tasks = list(bug.bug_tasks)
            chosen_task = self._choose_task(tasks, project)

            status = getattr(chosen_task, "status", None) if chosen_task else None
            state = self._normalize_state(status=status, bug=bug)

            labels = list(bug.tags) if hasattr(bug, "tags") else []

            return IssueData(
                title=bug.title,
                state=state,
                state_reason=status,
                labels=labels,
                raw={
                    "id": bug_id,
                    "title": bug.title,
                    "status": status,
                    "importance": (
                        getattr(chosen_task, "importance", None)
                        if chosen_task
                        else None
                    ),
                    "url": bug.web_link,
                    "labels": labels,
                },
            )
        except (NotFound, KeyError) as e:
            raise IssueNotFoundError(f"Launchpad bug {key} not found") from e
        except Unauthorized as e:
            raise APIError("Launchpad authentication/authorization failed") from e
        except (HTTPError, ServerError) as e:
            raise APIError(f"Launchpad API error while fetching bug {key}: {e}") from e
        except Exception as e:
            raise APIError(f"Failed to fetch Launchpad bug: {e}") from e

    def _parse_bug_id(self, key: str) -> int:
        """Parse and normalize bug ID"""
        s = str(key).strip()
        s = s.lstrip("#")

        if "+bug/" in s:
            s = s.split("+bug/")[-1].split("/")[0]

        try:
            return int(s)
        except ValueError as e:
            raise APIError(f"Invalid Launchpad bug id: {key!r}") from e

    def _choose_task(self, tasks: list, project: str) -> object | None:
        """Choose the most relevant task for the project"""
        if not tasks:
            return None

        if project:
            p = project.strip().lower()
            for t in tasks:
                for attr in (
                    "bug_target_name",
                    "bug_target_display_name",
                ):
                    v = getattr(t, attr, None)
                    if v and str(v).strip().lower() == p:
                        return t
                try:
                    if p in str(t).lower():
                        return t
                except Exception:
                    pass

        return tasks[0] if tasks else None

    def _normalize_state(self, status: str | None, bug: object) -> str:
        """Map Launchpad status to simple open/closed format"""
        # Trust is_complete if available
        is_complete = getattr(bug, "is_complete", None)
        if isinstance(is_complete, bool):
            return "closed" if is_complete else "open"

        if not status:
            return "open"

        closed_statuses = {
            "Fix Released",
            "Invalid",
            "Won't Fix",
            "Expired",
        }
        return "closed" if status in closed_statuses else "open"
