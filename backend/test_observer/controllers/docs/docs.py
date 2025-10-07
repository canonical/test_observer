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

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html


router: APIRouter = APIRouter()


@router.get("/openapi.json", include_in_schema=False)
async def custom_openapi(request: Request):
    app = request.app
    openapi_schema = app.openapi()

    # Iterate over all routes in the app
    for route in app.routes:
        if not hasattr(route, "dependant"):
            continue

        # Get security scopes for all dependencies
        security_scopes = []
        for dep in route.dependant.dependencies:
            security_scopes.extend(dep.security_scopes)
        if len(security_scopes) == 0:
            continue

        # Add security scopes to OpenAPI schema
        for method in route.methods:
            method_lower = method.lower()
            if (
                route.path in openapi_schema["paths"]
                and method_lower in openapi_schema["paths"][route.path]
            ):
                openapi_schema["paths"][route.path][method_lower]["x-permissions"] = (
                    security_scopes
                )

    return JSONResponse(openapi_schema)


@router.get("/docs", include_in_schema=False)
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
