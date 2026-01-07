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

from dataclasses import dataclass
from typing import Optional, Dict, Any, Iterable

from launchpadlib.launchpad import Launchpad

from lazr.restfulclient.errors import (  # type: ignore
    NotFound,
    Unauthorized,
    HTTPError,
    ServerError,
)

from test_observer.external_apis.exceptions import IssueNotFoundError, APIError, RateLimitError


@dataclass(frozen=True)
class _BugTaskView:
    """A small, JSON-serializable projection of a Launchpad BugTask."""
    target: str
    status: Optional[str]
    importance: Optional[str]
    assignee: Optional[str]


class LaunchpadClient:
    """
    Launchpad issue client.

    Notes:
    - Launchpad "issues" are "bugs". A bug has a global numeric ID (e.g. 1234567).
    - Status is usually per "bug task" (per project/package/distribution target).
    """

    def __init__(
        self,
        application_name: str = "test-observer-issue-sync",
        service_root: str = "production",
        version: str = "devel",
        timeout: int = 10,
        credentials_file: Optional[str] = None,
        cache_dir: Optional[str] = None,
        anonymous: bool = True,
    ):
        """
        Args:
            application_name: OAuth app name for launchpadlib
            service_root: "production" (or "staging" etc.)
            version: API version; commonly "devel"
            timeout: HTTP timeout (seconds)
            credentials_file: if set, uses OAuth login_with() and stores creds there
            cache_dir: optional cache dir used by launchpadlib (helps in CI)
            anonymous: if True -> login_anonymously (public read-only).
                       if False -> login_with (OAuth). If credentials_file is set,
                       we prefer OAuth regardless.
        """
        # launchpadlib supports anonymous login for read-only access :contentReference[oaicite:1]{index=1}
        self.application_name = application_name
        self.service_root = service_root
        self.version = version
        self.timeout = timeout
        self.credentials_file = credentials_file
        self.cache_dir = cache_dir
        self.anonymous = anonymous if credentials_file is None else False

        self.launchpad = self._login()

    def _login(self) -> Launchpad:
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

    def get_issue(self, project: str, key: str) -> Dict[str, Any]:
        """
        Fetch a Launchpad bug (issue) by bug ID.

        Args:
            project: used to select the most relevant BugTask status when possible.
                     (Examples: "ubuntu", "cloud-init", "launchpad", etc.)
                     If empty/unknown, we fall back to a best-effort task.
            key: bug id (string/int). Accepts "#123" or "123" or full URL.

        Returns:
            dict with keys 'title', 'state', 'raw'

        Raises:
            IssueNotFoundError: bug not found or not visible
            APIError: other failures
        """
        bug_id = self._parse_bug_id(key)

        try:
            bug = self.launchpad.bugs[bug_id]
        except NotFound as e:
            raise IssueNotFoundError(f"Launchpad bug {bug_id} not found") from e
        except Unauthorized as e:
            raise APIError("Launchpad authentication/authorization failed") from e
        except (HTTPError, ServerError) as e:
            raise APIError(f"Launchpad API error while fetching bug {bug_id}: {e}") from e
        except Exception as e:
            raise APIError(f"Unexpected Launchpad error while fetching bug {bug_id}: {e}") from e

        # Bug-level fields
        title = (getattr(bug, "title", "") or "").strip()
        description = getattr(bug, "description", None)
        web_link = getattr(bug, "web_link", None)

        # Task-level status is usually what people mean by "state"
        tasks = list(self._safe_iter(getattr(bug, "bug_tasks", []) or []))
        chosen_task = self._choose_task(tasks, project)

        status = getattr(chosen_task, "status", None) if chosen_task else None
        importance = getattr(chosen_task, "importance", None) if chosen_task else None
        assignee = None
        if chosen_task is not None:
            assignee_obj = getattr(chosen_task, "assignee", None)
            assignee = getattr(assignee_obj, "name", None) if assignee_obj else None

        state = self._normalize_state(status=status, bug=bug)

        raw = {
            "id": bug_id,
            "title": title,
            "description": description,
            "web_link": web_link,
            "status": status,
            "importance": importance,
            "assignee": assignee,
            "tags": list(getattr(bug, "tags", []) or []),
            "date_created": str(getattr(bug, "date_created", "")) or None,
            "date_last_updated": str(getattr(bug, "date_last_updated", "")) or None,
            "tasks": [
                _BugTaskView(
                    target=str(getattr(t, "bug_target_name", "") or getattr(t, "bug_target_display_name", "") or ""),
                    status=getattr(t, "status", None),
                    importance=getattr(t, "importance", None),
                    assignee=(getattr(getattr(t, "assignee", None), "name", None) if getattr(t, "assignee", None) else None),
                ).__dict__
                for t in tasks
            ],
        }

        return {
            "title": title,
            "state": state,
            "state_reason": status,  # keep status here for parity with GitHub shape
            "raw": raw,
        }

    def _parse_bug_id(self, key: str) -> int:
        s = str(key).strip()
        s = s.lstrip("#")

        # Accept full URL like https://bugs.launchpad.net/.../+bug/12345
        if "+bug/" in s:
            s = s.split("+bug/")[-1].split("/")[0]

        try:
            return int(s)
        except ValueError as e:
            raise APIError(f"Invalid Launchpad bug id: {key!r}") from e

    def _safe_iter(self, it: Iterable[Any]) -> Iterable[Any]:
        try:
            for x in it:
                yield x
        except Exception:
            # launchpadlib collections can sometimes lazily fetch; fail closed
            return

    def _choose_task(self, tasks: list[Any], project: str) -> Optional[Any]:
        if not tasks:
            return None
        if project:
            p = project.strip().lower()
            for t in tasks:
                # try a few likely fields
                for attr in ("bug_target_name", "bug_target_display_name"):
                    v = getattr(t, attr, None)
                    if v and str(v).strip().lower() == p:
                        return t
                # sometimes __str__ contains a URL-ish representation
                try:
                    if p in str(t).lower():
                        return t
                except Exception:
                    pass
        # fallback: first task
        return tasks[0]

    def _normalize_state(self, status: Optional[str], bug: Any) -> str:
        # If Launchpad provides is_complete, trust it.
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
