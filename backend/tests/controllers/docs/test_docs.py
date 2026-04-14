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

from test_observer.common.permissions import (
    authentication_checker,
    authentication_checker_browser_friendly,
    requires_authentication,
)
from test_observer.main import app
from tests.conftest import authenticate_user
from tests.data_generator import DataGenerator


def test_openapi_unauthenticated_auth_not_required(test_client: TestClient):
    """Test that unauthenticated access to OpenAPI endpoint works when authentication is not required"""
    try:
        app.dependency_overrides[requires_authentication] = lambda: False
        response = test_client.get("/openapi.json")
        assert response.status_code == 200
        assert "openapi" in response.json()
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_openapi_unauthenticated_auth_required(test_client: TestClient):
    """Test that unauthenticated access to OpenAPI endpoint returns 401 when authentication is required"""
    try:
        app.dependency_overrides[requires_authentication] = lambda: True
        response = test_client.get("/openapi.json")
        assert response.status_code == 401
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_openapi_authenticated_app_auth_not_required(test_client: TestClient, generator: DataGenerator):
    """
    Test that authenticated access to the OpenAPI endpoint works and returns schema
    when authentication is not required and an application is authenticated
    """
    try:
        app.dependency_overrides[requires_authentication] = lambda: False
        application = generator.gen_application(permissions=[])
        response = test_client.get("/openapi.json", headers={"Authorization": f"Bearer {application.api_key}"})
        assert response.status_code == 200
        assert "openapi" in response.json()
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_openapi_authenticated_user_auth_not_required(
    test_client: TestClient, generator: DataGenerator, create_session_cookie: Callable[[int], str]
):
    """
    Test that authenticated access to the OpenAPI endpoint works and returns schema
    when authentication is not required and a user is authenticated
    """
    try:
        app.dependency_overrides[requires_authentication] = lambda: False
        user = generator.gen_user()
        authenticate_user(test_client, user, generator, create_session_cookie)
        response = test_client.get("/openapi.json", headers={"X-CSRF-Token": "1"})
        assert response.status_code == 200
        assert "openapi" in response.json()
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_openapi_authenticated_app_auth_required(test_client: TestClient, generator: DataGenerator):
    """
    Test that authenticated access to the OpenAPI endpoint works and returns schema
    when authentication is required and an application is authenticated
    """
    try:
        app.dependency_overrides[requires_authentication] = lambda: True
        application = generator.gen_application(permissions=[])
        response = test_client.get("/openapi.json", headers={"Authorization": f"Bearer {application.api_key}"})
        assert response.status_code == 200
        assert "openapi" in response.json()
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_openapi_authenticated_user_auth_required(
    test_client: TestClient, generator: DataGenerator, create_session_cookie: Callable[[int], str]
):
    """
    Test that authenticated access to the OpenAPI endpoint works and returns schema
    when authentication is required and a user is authenticated
    """
    try:
        app.dependency_overrides[requires_authentication] = lambda: True
        user = generator.gen_user()
        authenticate_user(test_client, user, generator, create_session_cookie)
        response = test_client.get("/openapi.json", headers={"X-CSRF-Token": "1"})
        assert response.status_code == 200
        assert "openapi" in response.json()
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_docs_unauthenticated_auth_not_required(test_client: TestClient):
    """Test that unauthenticated access to docs endpoint works when authentication is not required"""
    try:
        app.dependency_overrides[requires_authentication] = lambda: False
        response = test_client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_docs_unauthenticated_auth_required(test_client: TestClient):
    """Test that unauthenticated access to docs endpoint returns 401 when authentication is required"""
    try:
        app.dependency_overrides[requires_authentication] = lambda: True
        response = test_client.get("/docs")
        assert response.status_code == 401
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_docs_authenticated_app_auth_not_required(test_client: TestClient, generator: DataGenerator):
    """
    Test that authenticated access to the docs endpoint works and returns HTML
    when authentication is not required and an application is authenticated
    """
    try:
        app.dependency_overrides[requires_authentication] = lambda: False
        application = generator.gen_application(permissions=[])
        response = test_client.get("/docs", headers={"Authorization": f"Bearer {application.api_key}"})
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_docs_authenticated_user_auth_not_required(
    test_client: TestClient, generator: DataGenerator, create_session_cookie: Callable[[int], str]
):
    """
    Test that authenticated access to the docs endpoint works and returns HTML
    when authentication is not required and a user is authenticated
    """
    try:
        app.dependency_overrides[requires_authentication] = lambda: False
        user = generator.gen_user()
        authenticate_user(test_client, user, generator, create_session_cookie)
        response = test_client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_docs_authenticated_app_auth_required(test_client: TestClient, generator: DataGenerator):
    """
    Test that authenticated access to the docs endpoint works and returns HTML
    when authentication is required and an application is authenticated
    """
    try:
        app.dependency_overrides[requires_authentication] = lambda: True
        application = generator.gen_application(permissions=[])
        response = test_client.get("/docs", headers={"Authorization": f"Bearer {application.api_key}"})
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_docs_authenticated_user_auth_required(
    test_client: TestClient, generator: DataGenerator, create_session_cookie: Callable[[int], str]
):
    """
    Test that authenticated access to the docs endpoint works and returns HTML
    when authentication is required and a user is authenticated
    """
    try:
        app.dependency_overrides[requires_authentication] = lambda: True
        user = generator.gen_user()
        authenticate_user(test_client, user, generator, create_session_cookie)
        # A browser request to the docs endpoint should work with a valid session cookie even without a CSRF token,
        # due to the browser-friendly dependencies used by the endpoint.
        # The point of this test is to check that we don't need the CSRF token
        response = test_client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_only_docs_browser_friendly(
    test_client: TestClient, generator: DataGenerator, create_session_cookie: Callable[[int], str]
):
    """
    Test that only the docs endpoint is browser-friendly and allows GET requests without a CSRF token
    when authentication is required and a user is authenticated.
    """
    try:
        user = generator.gen_user()
        authenticate_user(test_client, user, generator, create_session_cookie)

        # We override the authentication checker so that /openapi.json uses the browser-friendly version
        app.dependency_overrides[authentication_checker] = authentication_checker_browser_friendly

        # But the browser-friendly version should enforce that only /docs is allowed
        response = test_client.get("/openapi.json", headers={"X-CSRF-Token": "1"})
        assert response.status_code == 401
    finally:
        app.dependency_overrides.pop(authentication_checker, None)
