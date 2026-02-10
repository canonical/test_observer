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
import requests
import os
from typing import cast
from test_observer.external_apis.jira.jira_client import JiraClient
from test_observer.external_apis.launchpad.launchpad_client import LaunchpadClient
from test_observer.external_apis.exceptions import IssueNotFoundError


@pytest.mark.integration
class TestJiraClientIntegration:
    """Integration tests with real Jira sandbox API"""

    @pytest.mark.skipif(
        not all(
            [
                os.getenv("JIRA_CLOUD_ID"),
                os.getenv("JIRA_EMAIL"),
                os.getenv("JIRA_API_TOKEN"),
            ]
        ),
        reason="Jira credentials not configured in environment",
    )
    def test_get_real_jira_issue(self) -> None:
        """Test fetching a real Jira issue from public sandbox"""
        client = JiraClient(
            cloud_id=cast(str, os.getenv("JIRA_CLOUD_ID")),
            email=cast(str, os.getenv("JIRA_EMAIL")),
            api_token=cast(str, os.getenv("JIRA_API_TOKEN")),
        )
        result = client.get_issue("TO", "TO-169")

        assert result.title is not None
        assert result.state is not None
        assert result.raw is not None

    @pytest.mark.skipif(
        not all(
            [
                os.getenv("JIRA_CLOUD_ID"),
                os.getenv("JIRA_EMAIL"),
                os.getenv("JIRA_API_TOKEN"),
            ]
        ),
        reason="Jira credentials not configured in environment",
    )
    def test_get_nonexistent_jira_issue(self) -> None:
        """Test 404 handling"""
        client = JiraClient(
            cloud_id=cast(str, os.getenv("JIRA_CLOUD_ID")),
            email=cast(str, os.getenv("JIRA_EMAIL")),
            api_token=cast(str, os.getenv("JIRA_API_TOKEN")),
        )
        with pytest.raises(requests.exceptions.HTTPError):
            client.get_issue("DPE", "DPE-999999")


@pytest.mark.integration
class TestLaunchpadClientIntegration:
    """Integration tests with real Launchpad API"""

    def test_get_real_launchpad_bug(self) -> None:
        """Test fetching a real public Launchpad bug"""
        client = LaunchpadClient(anonymous=True)
        result = client.get_issue("ubuntu", "1")

        assert result.title is not None
        assert result.state in ("open", "closed")
        assert result.raw is not None

    def test_get_nonexistent_launchpad_bug(self) -> None:
        """Test 404 handling"""
        client = LaunchpadClient(anonymous=True)
        with pytest.raises(IssueNotFoundError):
            client.get_issue("ubuntu", "9999999999")
