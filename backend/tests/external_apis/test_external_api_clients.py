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

from unittest.mock import Mock, MagicMock, patch
import pytest

from test_observer.external_apis.github.github_client import GitHubClient
from test_observer.external_apis.jira.jira_client import JiraClient
from test_observer.external_apis.launchpad.launchpad_client import LaunchpadClient
from test_observer.external_apis.exceptions import (
    IssueNotFoundError,
    APIError,
    RateLimitError,
)


class TestGitHubClient:
    """Tests for GitHubClient"""

    def test_init_with_token(self) -> None:
        """Test GitHub client initialization with token"""
        with patch("test_observer.external_apis.github.github_client.Github"):
            client = GitHubClient(token="test_token")
            assert client.token == "test_token"

    def test_init_without_token(self) -> None:
        """Test GitHub client initialization without token"""
        with patch("test_observer.external_apis.github.github_client.Github"):
            client = GitHubClient()
            assert client.token is None

    def test_get_issue_success(self) -> None:
        """Test successful issue fetch"""
        mock_issue = Mock()
        mock_issue.title = "Test Issue"
        mock_issue.state = "open"
        mock_issue.id = 123
        mock_issue.number = 71
        mock_issue.html_url = "https://github.com/owner/repo/issues/71"

        mock_repo = Mock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github = Mock()
        mock_github.get_repo.return_value = mock_repo

        with patch(
            "test_observer.external_apis.github.github_client.Github",
            return_value=mock_github,
        ):
            client = GitHubClient(token="test_token")
            result = client.get_issue("owner/repo", "71")

            assert result["title"] == "Test Issue"
            assert result["state"] == "open"
            assert result["raw"]["number"] == 71
            mock_github.get_repo.assert_called_once_with("owner/repo")
            mock_repo.get_issue.assert_called_once_with(71)

    def test_get_issue_not_found(self) -> None:
        """Test issue not found (404)"""
        from github import GithubException

        mock_github = Mock()
        mock_github.get_repo.side_effect = GithubException(404, "Not Found")

        with patch(
            "test_observer.external_apis.github.github_client.Github",
            return_value=mock_github,
        ):
            client = GitHubClient(token="test_token")
            with pytest.raises(IssueNotFoundError):
                client.get_issue("owner/repo", "999")

    def test_get_issue_rate_limited(self) -> None:
        """Test rate limit handling"""
        from github import GithubException

        mock_github = Mock()
        error = GithubException(403, "API rate limit exceeded")
        mock_github.get_repo.side_effect = error

        with patch(
            "test_observer.external_apis.github.github_client.Github",
            return_value=mock_github,
        ):
            client = GitHubClient(token="test_token")
            with pytest.raises(RateLimitError):
                client.get_issue("owner/repo", "71")

    def test_get_issue_auth_failed(self) -> None:
        """Test authentication failure"""
        from github import GithubException

        mock_github = Mock()
        mock_github.get_repo.side_effect = GithubException(401, "Unauthorized")

        with patch(
            "test_observer.external_apis.github.github_client.Github",
            return_value=mock_github,
        ):
            client = GitHubClient(token="invalid_token")
            with pytest.raises(APIError, match="authentication failed"):
                client.get_issue("owner/repo", "71")


class TestJiraClient:
    """Tests for JiraClient"""

    def test_init_cloud_auth(self) -> None:
        """Test Jira client initialization with Cloud auth"""
        with patch("test_observer.external_apis.jira.jira_client.JIRA"):
            client = JiraClient(
                base_url="https://example.atlassian.net",
                email="user@example.com",
                api_token="token123",
            )
            assert client.base_url == "https://example.atlassian.net"

    def test_init_bearer_auth(self) -> None:
        """Test Jira client initialization with Bearer token"""
        with patch("test_observer.external_apis.jira.jira_client.JIRA"):
            client = JiraClient(
                base_url="https://jira.company.com",
                bearer_token="token123",
            )
            assert client.base_url == "https://jira.company.com"

    def test_normalize_issue_key_with_project(self) -> None:
        """Test issue key normalization with project"""
        with patch("test_observer.external_apis.jira.jira_client.JIRA"):
            client = JiraClient(base_url="https://example.atlassian.net")
            key = client._normalize_issue_key("TO", "123")
            assert key == "TO-123"

    def test_normalize_issue_key_with_hash(self) -> None:
        """Test issue key normalization with hash"""
        with patch("test_observer.external_apis.jira.jira_client.JIRA"):
            client = JiraClient(base_url="https://example.atlassian.net")
            key = client._normalize_issue_key("TO", "#123")
            assert key == "TO-123"

    def test_normalize_issue_key_full_key(self) -> None:
        """Test issue key normalization with full key"""
        with patch("test_observer.external_apis.jira.jira_client.JIRA"):
            client = JiraClient(base_url="https://example.atlassian.net")
            key = client._normalize_issue_key("TO", "TO-123")
            assert key == "TO-123"

    def test_normalize_state_done(self) -> None:
        """Test state normalization for done status"""
        with patch("test_observer.external_apis.jira.jira_client.JIRA"):
            client = JiraClient(base_url="https://example.atlassian.net")
            state = client._normalize_state(status_category="done")
            assert state == "closed"

    def test_normalize_state_with_resolution(self) -> None:
        """Test state normalization with resolution"""
        with patch("test_observer.external_apis.jira.jira_client.JIRA"):
            client = JiraClient(base_url="https://example.atlassian.net")
            state = client._normalize_state(resolution="Fixed")
            assert state == "closed"

    def test_normalize_state_open(self) -> None:
        """Test state normalization for open status"""
        with patch("test_observer.external_apis.jira.jira_client.JIRA"):
            client = JiraClient(base_url="https://example.atlassian.net")
            state = client._normalize_state(status_category="in_progress")
            assert state == "open"

    def test_get_issue_success(self) -> None:
        """Test successful Jira issue fetch"""
        mock_status = Mock()
        mock_status.name = "To Do"
        mock_status.statusCategory.key = "to_do"

        mock_fields = Mock()
        mock_fields.summary = "Test Issue"
        mock_fields.status = mock_status
        mock_fields.resolution = None

        mock_issue = Mock()
        mock_issue.key = "TO-123"
        mock_issue.fields = mock_fields
        mock_issue.permalink.return_value = "https://jira.atlassian.net/TO-123"

        mock_jira = Mock()
        mock_jira.issue.return_value = mock_issue

        with patch(
            "test_observer.external_apis.jira.jira_client.JIRA",
            return_value=mock_jira,
        ):
            client = JiraClient(
                base_url="https://example.atlassian.net",
                email="user@example.com",
                api_token="token",
            )
            result = client.get_issue("TO", "123")

            assert result["title"] == "Test Issue"
            assert result["state"] == "open"
            assert result["state_reason"] == "To Do"
            mock_jira.issue.assert_called_once_with("TO-123")

    def test_get_issue_not_found(self) -> None:
        """Test Jira issue not found"""
        from jira.exceptions import JIRAError

        mock_jira = Mock()

        # Create a real JIRAError and set status_code
        def raise_not_found(*_: object, **__: object) -> object:
            error = JIRAError("Not Found")
            error.status_code = 404
            raise error

        mock_jira.issue.side_effect = raise_not_found

        with patch(
            "test_observer.external_apis.jira.jira_client.JIRA",
            return_value=mock_jira,
        ):
            client = JiraClient(
                base_url="https://example.atlassian.net",
                email="user@example.com",
                api_token="token",
            )
            with pytest.raises(IssueNotFoundError):
                client.get_issue("TO", "999")

    def test_get_issue_rate_limited(self) -> None:
        """Test Jira rate limit"""
        from jira.exceptions import JIRAError

        mock_jira = Mock()

        # Create a real JIRAError and set status_code
        def raise_rate_limit(*_: object, **__: object) -> object:
            error = JIRAError("Rate Limited")
            error.status_code = 429
            raise error

        mock_jira.issue.side_effect = raise_rate_limit

        with patch(
            "test_observer.external_apis.jira.jira_client.JIRA",
            return_value=mock_jira,
        ):
            client = JiraClient(
                base_url="https://example.atlassian.net",
                email="user@example.com",
                api_token="token",
            )
            with pytest.raises(RateLimitError):
                client.get_issue("TO", "123")


class TestLaunchpadClient:
    """Tests for LaunchpadClient"""

    def test_init_anonymous(self) -> None:
        """Test anonymous initialization"""
        with patch("test_observer.external_apis.launchpad.launchpad_client.Launchpad"):
            client = LaunchpadClient(anonymous=True)
            assert client.anonymous is True

    def test_init_with_credentials(self) -> None:
        """Test initialization with credentials file"""
        with patch("test_observer.external_apis.launchpad.launchpad_client.Launchpad"):
            client = LaunchpadClient(
                anonymous=False,
                credentials_file="/path/to/credentials",
            )
            assert client.anonymous is False
            assert client.credentials_file == "/path/to/credentials"

    def test_parse_bug_id_simple(self) -> None:
        """Test bug ID parsing"""
        with patch("test_observer.external_apis.launchpad.launchpad_client.Launchpad"):
            client = LaunchpadClient(anonymous=True)
            bug_id = client._parse_bug_id("1234567")
            assert bug_id == 1234567

    def test_parse_bug_id_with_hash(self) -> None:
        """Test bug ID parsing with hash"""
        with patch("test_observer.external_apis.launchpad.launchpad_client.Launchpad"):
            client = LaunchpadClient(anonymous=True)
            bug_id = client._parse_bug_id("#1234567")
            assert bug_id == 1234567

    def test_parse_bug_id_invalid(self) -> None:
        """Test invalid bug ID raises error"""
        with patch("test_observer.external_apis.launchpad.launchpad_client.Launchpad"):
            client = LaunchpadClient(anonymous=True)
            with pytest.raises(APIError):
                client._parse_bug_id("invalid")

    def test_normalize_state_complete(self) -> None:
        """Test state normalization for complete bug"""
        mock_bug = Mock()
        mock_bug.is_complete = True

        with patch("test_observer.external_apis.launchpad.launchpad_client.Launchpad"):
            client = LaunchpadClient(anonymous=True)
            state = client._normalize_state(status=None, bug=mock_bug)
            assert state == "closed"

    def test_normalize_state_closed_status(self) -> None:
        """Test state normalization for closed status"""
        mock_bug = Mock(spec=["is_complete"])
        mock_bug.is_complete = None  # Don't set so it checks status instead

        with patch("test_observer.external_apis.launchpad.launchpad_client.Launchpad"):
            client = LaunchpadClient(anonymous=True)
            state = client._normalize_state(status="Fix Released", bug=mock_bug)
            assert state == "closed"

    def test_normalize_state_open(self) -> None:
        """Test state normalization for open status"""
        mock_bug = Mock()
        mock_bug.is_complete = False

        with patch("test_observer.external_apis.launchpad.launchpad_client.Launchpad"):
            client = LaunchpadClient(anonymous=True)
            state = client._normalize_state(status="New", bug=mock_bug)
            assert state == "open"

    def test_get_issue_success(self) -> None:
        """Test successful Launchpad bug fetch"""
        mock_task = Mock()
        mock_task.status = "New"
        mock_task.importance = "High"

        mock_bug = Mock()
        mock_bug.title = "Test Bug"
        mock_bug.is_complete = False
        mock_bug.bug_tasks = [mock_task]
        mock_bug.web_link = "https://bugs.launchpad.net/ubuntu/+bug/1234567"

        mock_launchpad = Mock()
        mock_launchpad.bugs = {1234567: mock_bug}

        with patch(
            "test_observer.external_apis.launchpad.launchpad_client.Launchpad"
        ) as mock_lp_class:
            mock_lp_class.login_anonymously.return_value = mock_launchpad

            client = LaunchpadClient(anonymous=True)
            result = client.get_issue("ubuntu", "1234567")

            assert result["title"] == "Test Bug"
            assert result["state"] == "open"
            assert result["state_reason"] == "New"

    def test_get_issue_not_found(self) -> None:
        """Test Launchpad bug not found"""
        from lazr.restfulclient.errors import NotFound  # type: ignore[import-untyped]

        mock_launchpad = MagicMock()
        mock_launchpad.bugs.__getitem__.side_effect = NotFound(
            response=Mock(status=404),
            content=b"Not Found",
        )

        with patch(
            "test_observer.external_apis.launchpad.launchpad_client.Launchpad"
        ) as mock_lp_class:
            mock_lp_class.login_anonymously.return_value = mock_launchpad

            client = LaunchpadClient(anonymous=True)
            with pytest.raises(IssueNotFoundError):
                client.get_issue("ubuntu", "9999999")

    def test_choose_task_matching_project(self) -> None:
        """Test choosing the correct task by project name"""
        mock_task1 = Mock()
        mock_task1.bug_target_name = "ubuntu"

        mock_task2 = Mock()
        mock_task2.bug_target_name = "debian"

        with patch("test_observer.external_apis.launchpad.launchpad_client.Launchpad"):
            client = LaunchpadClient(anonymous=True)
            chosen = client._choose_task([mock_task1, mock_task2], "ubuntu")
            assert chosen == mock_task1

    def test_choose_task_fallback_first(self) -> None:
        """Test fallback to first task when no project match"""
        mock_task1 = Mock()
        mock_task1.bug_target_name = "ubuntu"

        mock_task2 = Mock()
        mock_task2.bug_target_name = "debian"

        with patch("test_observer.external_apis.launchpad.launchpad_client.Launchpad"):
            client = LaunchpadClient(anonymous=True)
            chosen = client._choose_task([mock_task1, mock_task2], "unknown")
            assert chosen == mock_task1

    def test_choose_task_empty(self) -> None:
        """Test choose task with empty list"""
        with patch("test_observer.external_apis.launchpad.launchpad_client.Launchpad"):
            client = LaunchpadClient(anonymous=True)
            chosen = client._choose_task([], "ubuntu")
            assert chosen is None
