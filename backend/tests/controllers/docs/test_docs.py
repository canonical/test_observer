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
from test_observer.controllers.docs.docs import (
    APPLICATION_ONLY_OPERATIONS,
    PUBLIC_OPERATIONS,
    USER_ONLY_OPERATIONS,
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
    Test that only the docs endpoint is browser-friendly and allows GET requests without a CSRF token.
    This only applies when authentication is required
    """
    try:
        app.dependency_overrides[requires_authentication] = lambda: True
        user = generator.gen_user()
        authenticate_user(test_client, user, generator, create_session_cookie)

        # We override the authentication checker so that /openapi.json uses the browser-friendly version
        app.dependency_overrides[authentication_checker] = authentication_checker_browser_friendly

        # But the browser-friendly version should enforce that only /docs is allowed
        response = test_client.get("/openapi.json", headers={"X-CSRF-Token": "1"})
        assert response.status_code == 401
    finally:
        app.dependency_overrides.pop(authentication_checker, None)
        app.dependency_overrides.pop(requires_authentication, None)


EXPECTED_PUBLIC_OPERATIONS: list[tuple[str, str]] = [
    ("get", "/v1/auth/saml/login"),
    ("get", "/v1/auth/saml/logout"),
    ("post", "/v1/auth/saml/acs"),
    ("get", "/v1/auth/saml/sls"),
    ("post", "/v1/auth/saml/sls"),
    ("get", "/health/live"),
    ("get", "/health/ready"),
]

EXPECTED_USER_ONLY_OPERATIONS: list[tuple[str, str]] = [
    ("get", "/v1/users/me"),
    ("get", "/v1/users/me/notifications"),
    ("get", "/v1/users/me/notifications/count"),
    ("post", "/v1/users/me/notifications/{notification_id}/dismiss"),
]

EXPECTED_APPLICATION_ONLY_OPERATIONS: list[tuple[str, str]] = [
    ("get", "/v1/applications/me"),
    ("post", "/v1/applications/me/rotate"),
]

SESSION_ONLY_SECURITY: list[dict] = [{"sessionCookieAuth": [], "csrfTokenAuth": []}]
BEARER_ONLY_SECURITY: list[dict] = [{"bearerAuth": []}]

EXPECTED_SECURITY_SCHEMES: dict = {
    "bearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "description": "Application API key passed as an Authorization: Bearer header",
    },
    "sessionCookieAuth": {
        "type": "apiKey",
        "in": "cookie",
        "name": "session",
        "description": "Session cookie issued by the SAML login flow for browser users",
    },
    "csrfTokenAuth": {
        "type": "apiKey",
        "in": "header",
        "name": "X-CSRF-Token",
        "description": "CSRF protection header, required on all requests authenticated with the session cookie",
    },
}

EXPECTED_SECURITY_REQUIREMENTS: list[dict] = [
    {"bearerAuth": []},
    {"sessionCookieAuth": [], "csrfTokenAuth": []},
]


def test_openapi_security_declarations(test_client: TestClient):
    """
    Public operations (SAML flows and health probes) must not require any
    credentials, everything else must accept either an application API key
    (bearer token) or a user session (session cookie + CSRF header).
    User-only and application-only operations must document only the
    credential type they actually accept.
    """
    response = test_client.get("/openapi.json")
    schema = response.json()

    # Keep these expectations independent from the allowlists in docs.py so
    # that accidental additions or omissions there are caught here
    assert sorted(PUBLIC_OPERATIONS) == sorted(EXPECTED_PUBLIC_OPERATIONS)
    assert sorted(USER_ONLY_OPERATIONS) == sorted(EXPECTED_USER_ONLY_OPERATIONS)
    assert sorted(APPLICATION_ONLY_OPERATIONS) == sorted(EXPECTED_APPLICATION_ONLY_OPERATIONS)

    for method, path in EXPECTED_PUBLIC_OPERATIONS:
        assert schema["paths"][path][method]["security"] == []

    for method, path in EXPECTED_USER_ONLY_OPERATIONS:
        assert schema["paths"][path][method]["security"] == SESSION_ONLY_SECURITY

    for method, path in EXPECTED_APPLICATION_ONLY_OPERATIONS:
        assert schema["paths"][path][method]["security"] == BEARER_ONLY_SECURITY

    assert schema["security"] == EXPECTED_SECURITY_REQUIREMENTS
    assert schema["components"]["securitySchemes"] == EXPECTED_SECURITY_SCHEMES

    # Operations in none of the groups must inherit the root-level
    # requirements and must not opt out of them
    assert "security" not in schema["paths"]["/v1/artefacts/{artefact_id}"]["get"]
    assert "security" not in schema["paths"]["/v1/version"]["get"]
