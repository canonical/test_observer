#!/usr/bin/env python3

# Copyright 2026 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: Apache-2.0

"""Render the shared nginx config used by the backend charm and local Compose."""

import logging
import os
import re
import urllib.parse
from collections.abc import Sequence
from pathlib import Path

_CONTAINER_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
_AUTH_SECRET = re.compile(r"[A-Za-z0-9_-]+\Z")
_URL_NETLOC = re.compile(r"(?:[A-Za-z0-9.-]+|\[[0-9A-Fa-f:.]+\])(?::[0-9]{1,5})?\Z")
_URL_PATH = re.compile(r"[A-Za-z0-9._~/-]*\Z")
API_INTERNAL_PORT = 30001
API_METRICS_PORT = 9090
logger = logging.getLogger(__name__)


def render_nginx_config(
    template: str,
    *,
    port: int,
    swift_proxy_enabled: bool,
    auth_secret: str = "",
    swift_base_url: str = "",
    containers: Sequence[str] = (),
    verify_depth: int = 1,
) -> str:
    """Render nginx config and reject values that could alter its syntax."""
    validate_nginx_listen_port(port)

    swift_locations = ""
    swift_login_location = ""
    if swift_proxy_enabled:
        _validate_swift_config(auth_secret, swift_base_url, containers, verify_depth)
        swift_login_location = """
        location @swift_saml_login {
            return 302 $swift_login_url;
        }
"""
        base_url = swift_base_url.rstrip("/")
        locations = []
        for container in containers:
            public_path = f"/v1/swift/{container}"
            upstream_url = f"{base_url}/{container}/"
            locations.append(
                f"""
        location = {public_path} {{
            limit_except GET HEAD {{ deny all; }}
                return 301 {public_path}/$is_args$args;
        }}

        location ^~ {public_path}/ {{
            limit_except GET HEAD {{ deny all; }}
            auth_request /_internal/swift-auth;
            auth_request_set $keystone_token $upstream_http_x_keystone_token;
            auth_request_set $swift_login_url $upstream_http_x_swift_login_url;
            error_page 401 = @swift_saml_login;

            proxy_pass {upstream_url};
            proxy_http_version 1.1;
            proxy_buffering off;
            proxy_request_buffering off;
            proxy_read_timeout 3600s;
            proxy_send_timeout 3600s;
            send_timeout 3600s;
            proxy_set_header Connection "";
            proxy_set_header X-Auth-Token $keystone_token;
            proxy_set_header Authorization "";
            proxy_hide_header X-Auth-Token;
            proxy_hide_header X-Keystone-Token;
            proxy_set_header Host $proxy_host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;
            proxy_ssl_server_name on;
            proxy_ssl_name $proxy_host;
            proxy_ssl_verify on;
            proxy_ssl_verify_depth {verify_depth};
            proxy_ssl_trusted_certificate /etc/ssl/certs/ca-certificates.crt;
        }}
"""
            )
        swift_locations = "\n".join(locations)

    replacements = {
        "__SWIFT_PROXY_PORT__": str(port),
        "__SWIFT_PROXY_AUTH_SECRET__": auth_secret if swift_proxy_enabled else "",
        "__SWIFT_PROXY_LOGIN_LOCATION__": swift_login_location,
        "__SWIFT_PROXY_LOCATIONS__": swift_locations,
    }
    for marker in replacements:
        if marker not in template:
            raise ValueError(f"nginx template is missing required marker {marker}")
    marker_pattern = re.compile("|".join(re.escape(marker) for marker in replacements))
    return marker_pattern.sub(lambda match: replacements[match.group(0)], template)


def validate_nginx_listen_port(port: int) -> None:
    """Reject ports reserved by the API and its metrics server."""
    if not 1 <= port <= 65535:
        raise ValueError("nginx listen port must be between 1 and 65535")
    if port == API_INTERNAL_PORT:
        raise ValueError(f"nginx listen port must not overlap the API port {API_INTERNAL_PORT}")
    if port == API_METRICS_PORT:
        raise ValueError(f"nginx listen port must not overlap the metrics port {API_METRICS_PORT}")


def validate_keystone_auth_url(auth_url: str, *, setting_name: str = "OS_AUTH_URL") -> None:
    """Require Keystone authentication to use HTTPS and a valid host/port."""
    try:
        url = urllib.parse.urlsplit(auth_url)
        port = url.port
    except ValueError as exc:
        raise ValueError(f"{setting_name} is invalid") from exc

    if (
        url.scheme != "https"
        or not url.hostname
        or url.username
        or url.password
        or url.query
        or url.fragment
        or not _URL_NETLOC.fullmatch(url.netloc)
        or not _URL_PATH.fullmatch(url.path)
        or (port is not None and not 1 <= port <= 65535)
    ):
        raise ValueError(
            f"{setting_name} must be an HTTPS URL without credentials, query, or fragment"
        )


def validate_swift_config(
    swift_base_url: str,
    containers: Sequence[str],
    verify_depth: int,
    *,
    base_url_setting: str = "SWIFT_BASE_URL",
    containers_setting: str = "SWIFT_CONTAINERS",
    verify_depth_setting: str = "SWIFT_PROXY_SSL_VERIFY_DEPTH",
) -> None:
    """Validate the Swift URL, container names, and TLS verification depth."""
    try:
        url = urllib.parse.urlsplit(swift_base_url.rstrip("/"))
        port = url.port
    except ValueError as exc:
        raise ValueError(f"{base_url_setting} is invalid") from exc

    if (
        url.scheme != "https"
        or not url.hostname
        or url.username
        or url.password
        or url.query
        or url.fragment
        or not _URL_NETLOC.fullmatch(url.netloc)
        or not _URL_PATH.fullmatch(url.path)
        or any(segment in {".", ".."} for segment in url.path.split("/"))
        or (port is not None and not 1 <= port <= 65535)
    ):
        raise ValueError(
            f"{base_url_setting} must be an HTTPS URL without credentials, query, or fragment"
        )

    if not containers:
        raise ValueError(f"{containers_setting} must include at least one container")
    if len(containers) != len(set(containers)) or any(
        not _CONTAINER_NAME.fullmatch(container) for container in containers
    ):
        raise ValueError(f"{containers_setting} must contain unique, valid container names")
    if verify_depth < 1:
        raise ValueError(f"{verify_depth_setting} must be a positive integer")


def _validate_swift_config(
    auth_secret: str,
    swift_base_url: str,
    containers: Sequence[str],
    verify_depth: int,
) -> None:
    if not _AUTH_SECRET.fullmatch(auth_secret):
        raise ValueError("SWIFT_PROXY_AUTH_SECRET must contain only letters, digits, '_' or '-'")

    validate_swift_config(swift_base_url, containers, verify_depth)


def main() -> None:
    """Generate nginx config from local Compose environment variables."""
    enabled = os.getenv("SWIFT_PROXY_ENABLED", "false").lower() == "true"
    template_path = Path(os.getenv("SWIFT_PROXY_NGINX_TEMPLATE", "/etc/nginx/nginx.conf.template"))
    config_path = Path(os.getenv("SWIFT_PROXY_NGINX_CONFIG", "/etc/nginx/nginx.conf"))

    try:
        if enabled:
            validate_keystone_auth_url(os.getenv("OS_AUTH_URL", ""))
        rendered = render_nginx_config(
            template_path.read_text(encoding="utf-8"),
            port=int(os.getenv("SWIFT_PROXY_PORT", "30000")),
            swift_proxy_enabled=enabled,
            auth_secret=os.getenv("SWIFT_PROXY_AUTH_SECRET", ""),
            swift_base_url=os.getenv("SWIFT_BASE_URL", ""),
            containers=[
                container.strip()
                for container in os.getenv("SWIFT_CONTAINERS", "").split(",")
                if container.strip()
            ],
            verify_depth=int(os.getenv("SWIFT_PROXY_SSL_VERIFY_DEPTH", "1")),
        )
    except (OSError, ValueError) as exc:
        logger.error("Cannot generate nginx config: %s", exc)
        raise SystemExit(1) from exc

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(rendered, encoding="utf-8")
    config_path.chmod(0o600)


if __name__ == "__main__":
    main()
