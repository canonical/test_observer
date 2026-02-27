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

from test_observer.data_access.models import Issue
from test_observer.data_access.models_enums import IssueSource


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
