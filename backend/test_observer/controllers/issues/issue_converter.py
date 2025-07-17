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


import re
from pydantic import HttpUrl
from test_observer.data_access.models_enums import IssueSource


class IssueURLConverter:
    @staticmethod
    def from_url(url: HttpUrl) -> tuple[IssueSource, str, str]:
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
            match = re.match(r"^/browse/([A-Za-z]+)-([0-9]+)$", path)
            if match:
                return IssueSource.JIRA, match.group(1).upper(), match.group(2)

        elif host == "bugs.launchpad.net":
            match = re.match(r"^/([^/]+)/\+bug/(\d+)$", path)
            if match:
                return IssueSource.LAUNCHPAD, match.group(1).lower(), match.group(2)

        raise ValueError(
            f"Unrecognized issue URL format:\n"
            f"  host = '{host}'\n"
            f"  path = '{path}'\n\n"
            f"Expected formats:\n"
            f"  GitHub:     https://github.com/<owner>/<repo>/issues/<number>\n"
            f"  JIRA:       https://warthogs.atlassian.net/browse/<PROJECT-123>\n"
            f"  Launchpad:  https://bugs.launchpad.net/<project>/+bug/<number>"
        )

    @staticmethod
    def to_url(source: IssueSource, project: str, key: str) -> HttpUrl:
        """
        Convert (source, project, key) to a full issue URL.
        """
        if source == IssueSource.GITHUB:
            url = f"https://github.com/{project}/issues/{key}"

        elif source == IssueSource.JIRA:
            url = f"https://warthogs.atlassian.net/browse/{project}-{key}"

        elif source == IssueSource.LAUNCHPAD:
            url = f"https://bugs.launchpad.net/{project}/+bug/{key}"

        else:
            raise ValueError("Unrecognized issue source")
        
        return HttpUrl(url)
