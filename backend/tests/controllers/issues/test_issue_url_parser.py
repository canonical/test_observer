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


import pytest
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
