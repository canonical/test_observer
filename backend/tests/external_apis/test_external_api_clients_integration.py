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
from test_observer.external_apis.github.github_client import GitHubClient
from test_observer.external_apis.jira.jira_client import JiraClient
from test_observer.external_apis.launchpad.launchpad_client import LaunchpadClient
from test_observer.external_apis.exceptions import IssueNotFoundError


@pytest.mark.integration
class TestGitHubClientIntegration:
    """Integration tests with real GitHub API"""

    def test_get_real_github_issue(self) -> None:
        """Test fetching a real public GitHub issue"""
        client = GitHubClient()  # No token for public repos
        result = client.get_issue("canonical/test_observer", "71")

        assert result["title"] is not None
        assert len(result["title"]) > 0
        assert result["state"] in ("open", "closed")
        assert "raw" in result

    def test_get_nonexistent_github_issue(self) -> None:
        """Test 404 handling"""
        client = GitHubClient()
        with pytest.raises(IssueNotFoundError):
            client.get_issue("canonical/test_observer", "999999")


@pytest.mark.integration
class TestJiraClientIntegration:
    """Integration tests with real Jira sandbox API"""

    def test_get_real_jira_issue(self) -> None:
        """Test fetching a real Jira issue from public sandbox"""
        # Using public sandbox: https://warthogs-sandbox.atlassian.net/jira
        client = JiraClient(base_url="https://warthogs-sandbox.atlassian.net")
        # DPE is a public project in the sandbox
        result = client.get_issue("DPE", "9033")

        assert result["title"] is not None
        assert result["state"] in ("open", "closed")
        assert "raw" in result

    def test_get_nonexistent_jira_issue(self) -> None:
        """Test 404 handling"""
        client = JiraClient(base_url="https://warthogs-sandbox.atlassian.net")
        with pytest.raises(IssueNotFoundError):
            client.get_issue("DPE", "999999")


@pytest.mark.integration
class TestLaunchpadClientIntegration:
    """Integration tests with real Launchpad API"""

    def test_get_real_launchpad_bug(self) -> None:
        """Test fetching a real public Launchpad bug"""
        client = LaunchpadClient(anonymous=True)
        result = client.get_issue("ubuntu", "1")

        assert result["title"] is not None
        assert result["state"] in ("open", "closed")
        assert "raw" in result

    def test_get_nonexistent_launchpad_bug(self) -> None:
        """Test 404 handling"""
        client = LaunchpadClient(anonymous=True)
        with pytest.raises(IssueNotFoundError):
            client.get_issue("ubuntu", "9999999999")
