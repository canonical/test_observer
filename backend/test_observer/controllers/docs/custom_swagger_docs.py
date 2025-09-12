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

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html


router: APIRouter = APIRouter()


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
