# Copyright 2026 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from unittest.mock import Mock, patch

import pytest
import requests

from test_observer.external_apis.jira import JiraClient


@pytest.fixture
def jira_client() -> JiraClient:
    return JiraClient(cloud_id="test-cloud-id", email="bot@example.com", api_token="token")


class TestGetAccountIdByUsername:
    def test_returns_account_id_when_user_found(self, jira_client: JiraClient):
        mock_response = Mock()
        mock_response.json.return_value = [{"accountId": "abc123", "displayName": "Alice"}]
        mock_response.raise_for_status = Mock()

        with patch("test_observer.external_apis.jira.jira_client.requests.get", return_value=mock_response) as mock_get:
            result = jira_client.get_account_id_by_username("alice-lp")

        assert result == "abc123"
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        assert "alice-lp" in str(call_kwargs)

    def test_returns_none_when_no_user_found(self, jira_client: JiraClient):
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = Mock()

        with patch("test_observer.external_apis.jira.jira_client.requests.get", return_value=mock_response):
            result = jira_client.get_account_id_by_username("unknown-handle")

        assert result is None

    def test_propagates_http_error(self, jira_client: JiraClient):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("403 Forbidden")

        with (
            patch("test_observer.external_apis.jira.jira_client.requests.get", return_value=mock_response),
            pytest.raises(requests.exceptions.HTTPError),
        ):
            jira_client.get_account_id_by_username("alice-lp")
