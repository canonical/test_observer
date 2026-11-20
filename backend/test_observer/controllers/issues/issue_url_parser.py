# Copyright 2025 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import re
from urllib.parse import urlparse

import requests
from pydantic import HttpUrl

from test_observer.data_access.models_enums import IssueSource


def _resolve_launchpad_short_url(bug_id: str) -> tuple[str, str]:
    """
    Resolve a short Launchpad bug URL (launchpad.net/bugs/<id>) by following
    its redirect and extracting the project and key from the canonical URL.

    Returns:
        (project, key) extracted from the redirect target.
    Raises:
        ValueError if the redirect cannot be followed or parsed.
    """
    short_url = f"https://launchpad.net/bugs/{bug_id}"
    try:
        response = requests.head(short_url, allow_redirects=True, timeout=10)
        resolved_url = response.url
    except requests.RequestException as e:
        raise ValueError(f"Could not resolve Launchpad short URL {short_url}: {e}") from e

    parsed = urlparse(resolved_url)
    match = re.match(r"^/([^/]+)(?:/\+source/[^/]+)?/\+bug/(\d+)$", parsed.path)
    if match and parsed.hostname == "bugs.launchpad.net":
        return match.group(1).lower(), match.group(2)

    raise ValueError(
        f"Launchpad short URL {short_url} resolved to an unrecognised URL: {resolved_url}"
    )


def issue_source_project_key_from_url(url: HttpUrl) -> tuple[IssueSource, str, str]:
    """
    Extract (source, project, key) from an issue URL.
    Raises:
        ValueError if the URL does not match known formats.
    """
    host = url.host or ""
    path = url.path or ""

    if host == "github.com":
        match = re.match(r"^/([^/]+/[^/]+)/issues/(\d+)$", path)
        if match:
            return IssueSource.GITHUB, match.group(1).lower(), match.group(2)

    elif host == "warthogs.atlassian.net":
        match = re.match(r"^/browse/([A-Za-z]+)-([\d]+)$", path)
        if match:
            return IssueSource.JIRA, match.group(1).upper(), match.group(2)

    elif host == "bugs.launchpad.net":
        match = re.match(r"^/([^/]+)(?:/\+source/[^/]+)?/\+bug/(\d+)$", path)
        if match:
            return IssueSource.LAUNCHPAD, match.group(1).lower(), match.group(2)

    elif host == "launchpad.net":
        match = re.match(r"^/bugs/(\d+)$", path)
        if match:
            project, key = _resolve_launchpad_short_url(match.group(1))
            return IssueSource.LAUNCHPAD, project, key

    raise ValueError(
        f"Unrecognized issue URL format:\n"
        f"  host = '{host}'\n"
        f"  path = '{path}'\n\n"
        f"Expected formats:\n"
        f"  GitHub:     https://github.com/<owner>/<repo>/issues/<number>\n"
        f"  JIRA:       https://warthogs.atlassian.net/browse/<PROJECT-123>\n"
        f"  Launchpad:  https://bugs.launchpad.net/<project>/+bug/<number>\n"
        f"  Launchpad:  https://launchpad.net/bugs/<number>"
    )
