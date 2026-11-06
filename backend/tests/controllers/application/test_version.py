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

from fastapi import HTTPException
from fastapi.testclient import TestClient

from test_observer.common.permissions import local_or_authenticated
from test_observer.main import app
from tests.conftest import authenticate_user
from tests.data_generator import DataGenerator


def test_version_local_unauthenticated(test_client: TestClient):
    """Test that local unauthenticated access to version endpoint is allowed"""
    try:
        # Allow local access without authentication
        app.dependency_overrides[local_or_authenticated] = lambda: None
        response = test_client.get("/v1/version")
        assert response.status_code == 200
        assert "version" in response.json()
    finally:
        app.dependency_overrides.pop(local_or_authenticated, None)


def test_version_remote_unauthenticated(test_client: TestClient):
    """Test that remote unauthenticated access to version endpoint is denied"""
    try:
        # Simulate remote access without authentication by raising 401
        def remote_unauthenticated() -> None:
            raise HTTPException(status_code=401, detail="Not authenticated")

        app.dependency_overrides[local_or_authenticated] = remote_unauthenticated
        response = test_client.get("/v1/version")
        assert response.status_code == 401
    finally:
        app.dependency_overrides.pop(local_or_authenticated, None)


def test_version_remote_authenticated_with_app(test_client: TestClient, generator: DataGenerator):
    """Test that remote authenticated access with an application is allowed"""
    try:
        app.dependency_overrides[local_or_authenticated] = lambda: None
        application = generator.gen_application(permissions=[])
        response = test_client.get("/v1/version", headers={"Authorization": f"Bearer {application.api_key}"})
        assert response.status_code == 200
        assert "version" in response.json()
    finally:
        app.dependency_overrides.pop(local_or_authenticated, None)


def test_version_remote_authenticated_with_user(
    test_client: TestClient, generator: DataGenerator, create_session_cookie: Callable[[int], str]
):
    """Test that remote authenticated access with a user is allowed"""
    try:
        app.dependency_overrides[local_or_authenticated] = lambda: None
        user = generator.gen_user()
        authenticate_user(test_client, user, generator, create_session_cookie)
        response = test_client.get("/v1/version", headers={"X-CSRF-Token": "1"})
        assert response.status_code == 200
        assert "version" in response.json()
    finally:
        app.dependency_overrides.pop(local_or_authenticated, None)
