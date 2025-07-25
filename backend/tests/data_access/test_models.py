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

from test_observer.data_access.models_enums import IssueSource
from test_observer.data_access.models import Issue


@pytest.mark.parametrize(
    "source_project_key,expected",
    [
        # Unknown source
        (("unknown_source", "some-project", "some-key"), None),
        # Github
        (
            (IssueSource.GITHUB, "canonical/test_observer", "71"),
            "https://github.com/canonical/test_observer/issues/71",
        ),
        # Jira
        (
            (IssueSource.JIRA, "TO", "142"),
            "https://warthogs.atlassian.net/browse/TO-142",
        ),
        # Launchpad
        (
            (IssueSource.LAUNCHPAD, "abc", "123"),
            "https://bugs.launchpad.net/abc/+bug/123",
        ),
    ],
)
def test_issue_url(
    source_project_key: tuple[IssueSource, str, str],
    expected: str | None,
):
    try:
        source, project, key = source_project_key
        result = Issue(source=source, project=project, key=key).url
    except ValueError:
        assert expected is None
    else:
        assert result == expected
