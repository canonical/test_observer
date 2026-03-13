# Copyright 2025 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: Apache-2.0

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


def html_503() -> str:
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
