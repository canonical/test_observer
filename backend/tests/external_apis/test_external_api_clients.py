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
from unittest.mock import patch, Mock
from test_observer.external_apis.jira.jira_client import JiraClient
from test_observer.external_apis.launchpad.launchpad_client import LaunchpadClient
from test_observer.external_apis.models import IssueData
from test_observer.external_apis.exceptions import APIError


class TestJiraClient:
    """Tests for JiraClient with scoped service account tokens"""

    def test_init_cloud_auth(self) -> None:
        """Test JiraClient initialization with cloud ID"""
        client = JiraClient(
            cloud_id="test-cloud-id-123",
            email="test@example.com",
            api_token="test-token",
        )

        assert client.base_url == "https://api.atlassian.com/ex/jira/test-cloud-id-123"
        assert client.email == "test@example.com"
        assert client.api_token == "test-token"
        assert client.timeout == 30

    def test_init_with_custom_timeout(self) -> None:
        """Test JiraClient with custom timeout"""
        client = JiraClient(
            cloud_id="test-cloud-id",
            email="test@example.com",
            api_token="test-token",
            timeout=60,
        )

        assert client.timeout == 60

    def test_base_url_construction(self) -> None:
        """Test base URL construction with cloud ID"""
        cloud_id = "my-custom-cloud-id-123"
        client = JiraClient(
            cloud_id=cloud_id, email="test@example.com", api_token="test-token"
        )

        expected_url = f"https://api.atlassian.com/ex/jira/{cloud_id}"
        assert client.base_url == expected_url

    @patch("test_observer.external_apis.jira.jira_client.requests.get")
    def test_get_issue_success(self, mock_get: Mock) -> None:
        """Test successful issue retrieval"""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "key": "TEST-123",
            "fields": {
                "summary": "Test Issue Title",
                "status": {"name": "In Progress"},
            },
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = JiraClient(
            cloud_id="test-cloud", email="test@example.com", api_token="test-token"
        )

        result = client.get_issue("TEST", "TEST-123")

        assert isinstance(result, IssueData)
        assert result.title == "Test Issue Title"
        assert result.state == "In Progress"
        assert result.state_reason is None
        assert result.raw is not None

        # Verify the request was made correctly
        mock_get.assert_called_once()
        request = (
            "https://api.atlassian.com/ex/jira/test-cloud/rest/api/3/issue/TEST-123"
        )
        assert request in str(mock_get.call_args)

    @patch("test_observer.external_apis.jira.jira_client.requests.get")
    def test_get_issue_not_found(self, mock_get: Mock) -> None:
        """Test 404 error handling"""
        # Setup mock to raise HTTPError
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Not Found"
        )
        mock_get.return_value = mock_response

        client = JiraClient(
            cloud_id="test-cloud", email="test@example.com", api_token="test-token"
        )

        with pytest.raises(requests.exceptions.HTTPError):
            client.get_issue("TEST", "NOTFOUND-1")

    @patch("test_observer.external_apis.jira.jira_client.requests.get")
    def test_get_issue_rate_limited(self, mock_get: Mock) -> None:
        """Test rate limit error handling"""
        # Setup mock to raise HTTPError for rate limit
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "429 Too Many Requests"
        )
        mock_get.return_value = mock_response

        client = JiraClient(
            cloud_id="test-cloud", email="test@example.com", api_token="test-token"
        )

        with pytest.raises(requests.exceptions.HTTPError):
            client.get_issue("TEST", "TEST-1")


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
        mock_bug.tags = ["bug", "high-priority"]

        mock_launchpad = Mock()
        mock_launchpad.bugs = {1234567: mock_bug}

        with patch(
            "test_observer.external_apis.launchpad.launchpad_client.Launchpad"
        ) as mock_lp_class:
            mock_lp_class.login_anonymously.return_value = mock_launchpad

            client = LaunchpadClient(anonymous=True)
            result = client.get_issue("ubuntu", "1234567")

            assert result.title == "Test Bug"
            assert result.state == "open"
            assert result.state_reason == "New"
            assert result.labels == ["bug", "high-priority"]

