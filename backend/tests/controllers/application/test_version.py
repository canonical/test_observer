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

from collections.abc import Callable

from fastapi.testclient import TestClient

from test_observer.common.permissions import require_authentication
from test_observer.main import app
from tests.conftest import authenticate_user
from tests.data_generator import DataGenerator


def test_version_unauthenticated_auth_not_required(test_client: TestClient):
    """Test that unauthenticated access to version endpoint works when authentication is not required"""
    try:
        app.dependency_overrides[require_authentication] = lambda: False
        response = test_client.get("/v1/version")
        assert response.status_code == 200
        assert "version" in response.json()
    finally:
        app.dependency_overrides.pop(require_authentication, None)


def test_version_unauthenticated_auth_required(test_client: TestClient):
    """Test that unauthenticated access to version endpoint returns 401 when authentication is required"""
    try:
        app.dependency_overrides[require_authentication] = lambda: True
        response = test_client.get("/v1/version")
        assert response.status_code == 401
    finally:
        app.dependency_overrides.pop(require_authentication, None)


def test_version_authenticated_auth_not_required(
    test_client: TestClient, generator: DataGenerator, create_session_cookie: Callable[[int], str]
):
    """
    Test that authenticated access to version endpoint works and returns version
    when authentication is not required
    """
    try:
        app.dependency_overrides[require_authentication] = lambda: False

        application = generator.gen_application(permissions=[])
        response = test_client.get("/v1/version", headers={"Authorization": f"Bearer {application.api_key}"})
        assert response.status_code == 200
        assert "version" in response.json()

        user = generator.gen_user()
        authenticate_user(test_client, user, generator, create_session_cookie)
        response = test_client.get("/v1/version", headers={"X-CSRF-Token": "1"})
        assert response.status_code == 200
        assert "version" in response.json()
    finally:
        app.dependency_overrides.pop(require_authentication, None)


def test_version_authenticated_auth_required(
    test_client: TestClient, generator: DataGenerator, create_session_cookie: Callable[[int], str]
):
    """
    Test that authenticated access to version endpoint works and returns version
    when authentication is required
    """
    try:
        app.dependency_overrides[require_authentication] = lambda: True

        application = generator.gen_application(permissions=[])
        response = test_client.get("/v1/version", headers={"Authorization": f"Bearer {application.api_key}"})
        assert response.status_code == 200
        assert "version" in response.json()

        user = generator.gen_user()
        authenticate_user(test_client, user, generator, create_session_cookie)
        response = test_client.get("/v1/version", headers={"X-CSRF-Token": "1"})
        assert response.status_code == 200
        assert "version" in response.json()
    finally:
        app.dependency_overrides.pop(require_authentication, None)
