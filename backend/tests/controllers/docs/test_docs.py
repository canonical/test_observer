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

import re
from collections.abc import Callable

from fastapi.testclient import TestClient

from test_observer.common.permissions import (
    authentication_checker,
    authentication_checker_browser_friendly,
    requires_authentication,
)
from test_observer.controllers.docs.docs import PUBLIC_OPERATIONS, USER_ONLY_OVERRIDES
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

    The sets below must cover *all* operations in the schema that override the
    root-level security requirements, so a new endpoint classified as public,
    user-only or application-only fails here unless the expectations are
    updated deliberately.
    """
    response = test_client.get("/openapi.json")
    schema = response.json()

    assert sorted(PUBLIC_OPERATIONS) == sorted(EXPECTED_PUBLIC_OPERATIONS)

    def operations_with_security(security: list[dict]) -> set[tuple[str, str]]:
        return {
            (method, path)
            for path, operations in schema["paths"].items()
            for method, operation in operations.items()
            if isinstance(operation, dict) and operation.get("security") == security
        }

    assert operations_with_security([]) == set(EXPECTED_PUBLIC_OPERATIONS)
    assert operations_with_security(SESSION_ONLY_SECURITY) == set(EXPECTED_USER_ONLY_OPERATIONS)
    assert operations_with_security(BEARER_ONLY_SECURITY) == set(EXPECTED_APPLICATION_ONLY_OPERATIONS)

    assert schema["security"] == EXPECTED_SECURITY_REQUIREMENTS
    assert schema["components"]["securitySchemes"] == EXPECTED_SECURITY_SCHEMES
    assert "REQUIRE_AUTHENTICATION" in schema["info"]["description"]

    # Every allowlist/override entry must exist in the schema and match its
    # documented classification, so stale entries fail here (KeyError or
    # mismatch) rather than silently disappearing from the documentation
    for method, path in PUBLIC_OPERATIONS:
        assert schema["paths"][path][method].get("security") == []
    for method, path in USER_ONLY_OVERRIDES:
        assert schema["paths"][path][method].get("security") == SESSION_ONLY_SECURITY

    # Exhaustively, every operation either inherits the root-level security
    # requirements (no operation-level security key) or declares one of the
    # documented requirements; no other value may appear anywhere
    for operations in schema["paths"].values():
        for operation in operations.values():
            if isinstance(operation, dict) and "responses" in operation:
                assert "security" not in operation or operation["security"] in (
                    [],
                    SESSION_ONLY_SECURITY,
                    BEARER_ONLY_SECURITY,
                )


def _instantiate_path(path: str) -> str:
    """Replace path parameters (e.g. {notification_id}) with a dummy value."""
    return re.sub(r"\{[^}]+\}", "1", path)


def test_user_only_operations_reject_application_credentials(test_client: TestClient, generator: DataGenerator):
    """
    Operations documented as session-only must actually reject application
    credentials, so that the specification matches the effective behaviour.
    """
    try:
        app.dependency_overrides[requires_authentication] = lambda: True
        application = generator.gen_application(permissions=[])
        headers = {"Authorization": f"Bearer {application.api_key}"}
        for method, path in EXPECTED_USER_ONLY_OPERATIONS:
            response = test_client.request(method, _instantiate_path(path), headers=headers)
            # Routes that also take the application dependency explicitly
            # reject it with 403, routes that ignore it answer 401 like for
            # any other unauthenticated request. Neither may succeed.
            expected_status = 403 if (method, path) in USER_ONLY_OVERRIDES else 401
            assert response.status_code == expected_status, f"{method} {path} returned {response.status_code}"
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_application_only_operations_reject_user_sessions(
    test_client: TestClient, generator: DataGenerator, create_session_cookie: Callable[[int], str]
):
    """
    Operations documented as application-only must actually reject user
    sessions, so that the specification matches the effective behaviour.
    """
    try:
        app.dependency_overrides[requires_authentication] = lambda: True
        user = generator.gen_user()
        authenticate_user(test_client, user, generator, create_session_cookie)
        for method, path in EXPECTED_APPLICATION_ONLY_OPERATIONS:
            response = test_client.request(method, _instantiate_path(path), headers={"X-CSRF-Token": "1"})
            assert response.status_code == 401, f"{method} {path} returned {response.status_code}"
    finally:
        app.dependency_overrides.pop(requires_authentication, None)
