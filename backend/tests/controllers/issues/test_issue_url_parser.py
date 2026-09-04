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

import pytest
import requests_mock as req_mock
from pydantic import HttpUrl

from test_observer.controllers.issues.issue_url_parser import (
    issue_source_project_key_from_url,
)
from test_observer.data_access.models_enums import IssueSource


@pytest.mark.parametrize(
    "url,expected",
    [
        # Unknown domain
        ("https://unknown.com/canonical/test_observer/issues/71", None),
        # Bad github format
        ("https://github.com/unknown", None),
        # Bad github project
        ("https://github.com/canonical/issues/71", None),
        # Bad github key
        ("https://github.com/canonical/test_observer/issues/abc", None),
        # Good github
        (
            "https://github.com/canonical/test_observer/issues/71",
            (IssueSource.GITHUB, "canonical/test_observer", "71"),
        ),
        # Lowercase github project
        (
            "https://github.com/canonical/Test_Observer/issues/71",
            (IssueSource.GITHUB, "canonical/test_observer", "71"),
        ),
        # Bad jira format
        ("https://warthogs.atlassian.net/unknown", None),
        # Bad jira project
        ("https://warthogs.atlassian.net/browse/000-142", None),
        # Bad jira key
        ("https://warthogs.atlassian.net/browse/TS-ABC", None),
        # Good jira
        (
            "https://warthogs.atlassian.net/browse/TS-142",
            (IssueSource.JIRA, "TS", "142"),
        ),
        # Uppercase jira project
        (
            "https://warthogs.atlassian.net/browse/ts-142",
            (IssueSource.JIRA, "TS", "142"),
        ),
        # Bad launchpad format
        ("https://bugs.launchpad.net/unknown", None),
        # Bad launchpad project
        ("https://bugs.launchpad.net/abc/abc/*bug/123", None),
        # Bad launchpad key
        ("https://bugs.launchpad.net/abc/+bug/abc", None),
        # Good launchpad
        (
            "https://bugs.launchpad.net/abc/+bug/123",
            (IssueSource.LAUNCHPAD, "abc", "123"),
        ),
        (
            "https://bugs.launchpad.net/ubuntu/+source/linux-meta/+bug/2137746",
            (IssueSource.LAUNCHPAD, "ubuntu", "2137746"),
        ),
        # Lowercase launchpad project
        (
            "https://bugs.launchpad.net/ABC/+bug/123",
            (IssueSource.LAUNCHPAD, "abc", "123"),
        ),
        # Accept http
        (
            "http://github.com/canonical/test_observer/issues/71",
            (IssueSource.GITHUB, "canonical/test_observer", "71"),
        ),
        # Ignore query params
        (
            "http://github.com/canonical/test_observer/issues/71?some=param",
            (IssueSource.GITHUB, "canonical/test_observer", "71"),
        ),
    ],
)
def test_from_url(url: str, expected: tuple[IssueSource, str, str] | None):
    try:
        result = issue_source_project_key_from_url(HttpUrl(url))
    except ValueError:
        assert expected is None
    else:
        assert result == expected


def test_launchpad_short_url_resolves_project():
    """launchpad.net/bugs/<id> should follow the redirect and return the project."""
    with req_mock.Mocker() as m:
        m.head(
            "https://launchpad.net/bugs/1951586",
            status_code=301,
            headers={"Location": "https://bugs.launchpad.net/netplan/+bug/1951586"},
        )
        m.head(
            "https://bugs.launchpad.net/netplan/+bug/1951586",
            status_code=200,
        )
        result = issue_source_project_key_from_url(HttpUrl("https://launchpad.net/bugs/1951586"))
    assert result == (IssueSource.LAUNCHPAD, "netplan", "1951586")


def test_launchpad_short_url_with_source_package():
    """+source/ paths in the resolved URL are handled correctly."""
    with req_mock.Mocker() as m:
        m.head(
            "https://launchpad.net/bugs/2137746",
            status_code=301,
            headers={"Location": "https://bugs.launchpad.net/ubuntu/+source/linux-meta/+bug/2137746"},
        )
        m.head(
            "https://bugs.launchpad.net/ubuntu/+source/linux-meta/+bug/2137746",
            status_code=200,
        )
        result = issue_source_project_key_from_url(HttpUrl("https://launchpad.net/bugs/2137746"))
    assert result == (IssueSource.LAUNCHPAD, "ubuntu", "2137746")


def test_launchpad_short_url_bad_key():
    """Non-numeric bug ID in launchpad.net/bugs/ path raises ValueError."""
    with pytest.raises(ValueError):
        issue_source_project_key_from_url(HttpUrl("https://launchpad.net/bugs/abc"))


def test_launchpad_short_url_unknown_path():
    """Unrecognised launchpad.net path raises ValueError."""
    with pytest.raises(ValueError):
        issue_source_project_key_from_url(HttpUrl("https://launchpad.net/unknown/1951586"))


def test_launchpad_short_url_network_error():
    """Network failure while resolving the redirect raises ValueError."""
    import requests

    with req_mock.Mocker() as m:
        m.head("https://launchpad.net/bugs/1951586", exc=requests.ConnectionError("network down"))
        with pytest.raises(ValueError, match="Could not resolve"):
            issue_source_project_key_from_url(HttpUrl("https://launchpad.net/bugs/1951586"))


def test_launchpad_short_url_unexpected_redirect_target():
    """If the redirect resolves to an unexpected URL, ValueError is raised."""
    with req_mock.Mocker() as m:
        m.head(
            "https://launchpad.net/bugs/1951586",
            status_code=301,
            headers={"Location": "https://example.com/unexpected"},
        )
        m.head("https://example.com/unexpected", status_code=200)
        with pytest.raises(ValueError, match="unrecognised URL"):
            issue_source_project_key_from_url(HttpUrl("https://launchpad.net/bugs/1951586"))
