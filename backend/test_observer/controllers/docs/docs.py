# Copyright 2025 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from collections.abc import Iterator

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.dependencies.models import Dependant
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.routing import APIRoute

from test_observer.common.permissions import authentication_checker, authentication_checker_browser_friendly
from test_observer.controllers.applications.application_injection import get_current_application
from test_observer.users.user_injection import get_current_user, get_current_user_browser_friendly

router: APIRouter = APIRouter()

SECURITY_SCHEMES: dict = {
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

ROOT_SECURITY_REQUIREMENTS: list[dict] = [
    {"bearerAuth": []},
    {"sessionCookieAuth": [], "csrfTokenAuth": []},
]

SESSION_ONLY_SECURITY: list[dict] = [{"sessionCookieAuth": [], "csrfTokenAuth": []}]
BEARER_ONLY_SECURITY: list[dict] = [{"bearerAuth": []}]
NO_SECURITY: list[dict] = []

# Operations without authentication dependencies that must work before login or
# without credentials (SAML flows and local health probes). They opt out of the
# root-level security requirements.
#
# This is an explicit allowlist, not the source of truth: build_openapi_schema
# classifies every operation from its route dependencies. An operation without
# authentication dependencies is only documented as public if it is listed
# here; tests in tests/controllers/docs/test_docs.py enforce that this list
# matches the actual routes.
PUBLIC_OPERATIONS: tuple[tuple[str, str], ...] = (
    ("get", "/v1/auth/saml/login"),
    ("get", "/v1/auth/saml/logout"),
    ("post", "/v1/auth/saml/acs"),
    ("get", "/v1/auth/saml/sls"),
    ("post", "/v1/auth/saml/sls"),
    ("get", "/health/live"),
    ("get", "/health/ready"),
)

# Operations whose route dependencies accept both credential types, but whose
# handlers explicitly reject applications with a 403, so they effectively only
# accept a user session and must be documented as such. A handler that starts
# accepting applications for real makes an entry here stale; tests in
# tests/controllers/docs/test_docs.py detect that.
USER_ONLY_OVERRIDES: tuple[tuple[str, str], ...] = (
    ("get", "/v1/users/me/notifications"),
    ("get", "/v1/users/me/notifications/count"),
    ("post", "/v1/users/me/notifications/{notification_id}/dismiss"),
)


def _iter_dependency_calls(dependant: Dependant) -> Iterator:
    """Yield the callables of the dependant and all its (transitive) sub-dependencies."""
    yield dependant.call
    for sub_dependency in dependant.dependencies:
        yield from _iter_dependency_calls(sub_dependency)


def classify_route_auth(route: APIRoute) -> str:
    """
    Classify which credential types a route accepts, based on its dependencies.

    Returns one of:
    - "user": accepts a user session only (session cookie + CSRF header)
    - "application": accepts an application API key (bearer token) only
    - "both": accepts either credential type
    - "public": has no authentication dependencies at all
    """
    calls = set(_iter_dependency_calls(route.dependant))
    accepts_user = bool({get_current_user, get_current_user_browser_friendly} & calls)
    accepts_application = get_current_application in calls
    if accepts_user and accepts_application:
        return "both"
    if accepts_user:
        return "user"
    if accepts_application:
        return "application"
    return "public"


def _apply_operation_security(openapi_schema: dict, route: APIRoute, auth: str) -> None:
    """Set the operation-level security requirements for a route's operations."""
    for method in route.methods:
        method_lower = method.lower()
        if route.path not in openapi_schema["paths"] or method_lower not in openapi_schema["paths"][route.path]:
            # Route is not part of the published schema (e.g. include_in_schema=False)
            continue

        operation = openapi_schema["paths"][route.path][method_lower]

        if (method_lower, route.path) in USER_ONLY_OVERRIDES:
            operation["security"] = SESSION_ONLY_SECURITY
        elif auth == "public":
            operation["security"] = NO_SECURITY
        elif auth == "user":
            # Session-only operations must not advertise the root-level bearer
            # alternative, which they reject
            operation["security"] = SESSION_ONLY_SECURITY
        elif auth == "application":
            # Bearer-only operations must not advertise the root-level session
            # alternative, which they reject
            operation["security"] = BEARER_ONLY_SECURITY
        # auth == "both": inherit the root-level requirements


def build_openapi_schema(app: FastAPI) -> dict:
    openapi_schema = app.openapi()

    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {}).update(SECURITY_SCHEMES)
    openapi_schema["security"] = ROOT_SECURITY_REQUIREMENTS

    # Classify every route by the credential types it accepts and set the
    # operation-level security requirements accordingly. Operations that accept
    # either credential type inherit the root-level requirements.
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        _apply_operation_security(openapi_schema, route, classify_route_auth(route))

    # Iterate over all routes in the app to add permissions
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue

        # Get security scopes for all dependencies
        security_scopes: list[str] = []
        for dep in route.dependant.dependencies:
            security_scopes.extend(dep.oauth_scopes)

        if len(security_scopes) == 0:
            continue

        # Add security scopes to OpenAPI schema
        for method in route.methods:
            method_lower = method.lower()
            if route.path in openapi_schema["paths"] and method_lower in openapi_schema["paths"][route.path]:
                openapi_schema["paths"][route.path][method_lower]["x-permissions"] = security_scopes

    return openapi_schema


@router.get(
    "/openapi.json",
    include_in_schema=False,
    dependencies=[Depends(authentication_checker)],
)
async def custom_openapi(request: Request):
    app = request.app
    openapi_schema = build_openapi_schema(app)

    return JSONResponse(openapi_schema)


@router.get(
    "/docs",
    include_in_schema=False,
    dependencies=[Depends(authentication_checker_browser_friendly)],
)
async def custom_swagger_ui_html():
    html = get_swagger_ui_html(openapi_url="/openapi.json", title="API Documentation")

    # Inject custom script that overrides the global fetch to
    # add X-CSRF-TOKEN header to requests made through swagger docs
    custom_script = """
    <script>
    // Override the global fetch to add a header
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        let [url, config] = args;
        config = config || {};
        config.headers = config.headers || {};
        config.headers['X-CSRF-TOKEN'] = '1';
        args[1] = config;
        return originalFetch.apply(this, args);
    };
    </script>
    """

    html_content = html.body.decode()
    # Insert the script BEFORE the SwaggerUIBundle initialization
    html_content = html_content.replace(
        '<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>',
        f'<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>\n{custom_script}',
    )

    return HTMLResponse(content=html_content)
