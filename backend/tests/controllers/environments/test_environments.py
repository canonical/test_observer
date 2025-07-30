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

from fastapi.testclient import TestClient


def test_get_environments(test_client: TestClient):
    """Test getting environments endpoint"""
    response = test_client.get("/v1/environments")

    assert response.status_code == 200
    data = response.json()
    assert "environments" in data
    assert isinstance(data["environments"], list)


def test_get_environments_response_format(test_client: TestClient):
    """Test response format"""
    response = test_client.get("/v1/environments")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "environments" in data
