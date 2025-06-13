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

"""Module for generating a NGINX configuration allows for the frontend application to connect to the backend."""

def nginx_config(base_uri: str) -> str:
    """Generate nginx configuration for the frontend."""
    return f"""
    server {{
        listen       80;
        server_name  localhost;

        location / {{
            root   /usr/share/nginx/html;
            index  index.html index.htm;
            try_files $uri $uri/ /index.html =404;

            # Ensure no caching
            expires -1;
            add_header Cache-Control "no-store, no-cache, must-revalidate, post-check=0, pre-check=0";

            sub_filter 'http://localhost:30000/' '{base_uri}';
            sub_filter_once on;
        }}

        error_page   500 502 503 504  /50x.html;
        location = /50x.html {{
            root   /usr/share/nginx/html;
        }}
    }}
    """


def nginx_503_config() -> str:
    """Generate nginx configuration for a 503 Service Unavailable response."""
    return """
    server {
        listen 80 default_server;
        server_name _;
        return 503;
        error_page 503 @maintenance;

        location @maintenance {
            rewrite ^(.*)$ /503.html break;
            root /usr/share/nginx/html;

            # Ensure no caching
            expires -1;
            add_header Cache-Control "no-store, no-cache, must-revalidate, post-check=0, pre-check=0";
        }
    }
    """


def html_503(self) -> str:
    """Return a 503 response page."""
    return """
    <html>
        <head>
            <title>503 Service Unavailable</title>
        </head>
        <body>
            <h1>503 Service Unavailable</h1>
            <p>Backend not yet configured.</p>
        </body>
    </html>
    """
