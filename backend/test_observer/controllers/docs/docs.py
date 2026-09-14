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

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.routing import APIRoute

from test_observer.common.permissions import authentication_checker, authentication_checker_browser_friendly

router: APIRouter = APIRouter()

SECURITY_SCHEMES: dict = {
    "bearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "description": "Application API key passed as an Authorization: Bearer header",
    }
}

# Operations without authentication dependencies that must work before login
# or without credentials (SAML flows and local health probes). They opt out of
# the root-level bearer requirement.
PUBLIC_OPERATIONS: tuple[tuple[str, str], ...] = (
    ("get", "/v1/auth/saml/login"),
    ("get", "/v1/auth/saml/logout"),
    ("post", "/v1/auth/saml/acs"),
    ("get", "/v1/auth/saml/sls"),
    ("post", "/v1/auth/saml/sls"),
    ("get", "/health/live"),
    ("get", "/health/ready"),
)


def build_openapi_schema(app: FastAPI) -> dict:
    openapi_schema = app.openapi()

    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {}).update(SECURITY_SCHEMES)
    openapi_schema["security"] = [{"bearerAuth": []}]

    for method, path in PUBLIC_OPERATIONS:
        if path in openapi_schema["paths"] and method in openapi_schema["paths"][path]:
            openapi_schema["paths"][path][method]["security"] = []

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
