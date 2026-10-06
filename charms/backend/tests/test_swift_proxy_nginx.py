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

from pathlib import Path

import pytest
from swift_proxy_nginx import (
    render_nginx_config,
    validate_keystone_auth_url,
)

TEMPLATE_PATH = Path(__file__).parents[1] / "src" / "templates" / "nginx.conf"


@pytest.fixture
def template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def test_render_without_swift_proxy_removes_all_markers(template: str) -> None:
    """Render a regular API-only nginx configuration."""
    rendered = render_nginx_config(template, port=30000, swift_proxy_enabled=False)

    assert "listen 30000;" in rendered
    assert "client_max_body_size 10m;" in rendered
    assert "/v1/swift/" not in rendered
    assert "__SWIFT_PROXY_" not in rendered


def test_render_swift_locations_and_preserve_marker_text_in_secret(template: str) -> None:
    """Render configured Swift containers without recursively replacing values."""
    marker_secret = "local__SWIFT_PROXY_LOGIN_LOCATION__secret"

    rendered = render_nginx_config(
        template,
        port=30000,
        swift_proxy_enabled=True,
        auth_secret=marker_secret,
        swift_base_url="https://swift.example/v1/AUTH_project",
        containers=["artifacts", "logs"],
    )

    assert 'X-Swift-Proxy-Auth "local__SWIFT_PROXY_LOGIN_LOCATION__secret";' in rendered
    assert "proxy_set_header Cookie $http_cookie;" in rendered
    assert 'proxy_set_header Cookie "";' in rendered
    assert "location ^~ /v1/swift/artifacts/" in rendered
    assert "location ^~ /v1/swift/logs/" in rendered
    assert rendered.count("limit_except GET HEAD { deny all; }") == 4
    assert "if ($request_method" not in rendered
    assert (
        "proxy_pass https://swift.example/v1/AUTH_project/artifacts/;"
        in rendered
    )
    assert "return 301 /v1/swift/artifacts/$is_args$args;" in rendered
    assert "return 302 $swift_login_url;" in rendered
    assert "__SWIFT_PROXY_PORT__" not in rendered


@pytest.mark.parametrize(
    ("auth_secret", "swift_base_url", "containers", "message"),
    [
        (
            "bad secret",
            "https://swift.example/v1/AUTH_project",
            ["artifacts"],
            "SWIFT_PROXY_AUTH_SECRET",
        ),
        (
            "secret",
            "http://swift.example/v1/AUTH_project",
            ["artifacts"],
            "SWIFT_BASE_URL",
        ),
        (
            "secret",
            "https://swift.example/v1/AUTH_project",
            ["../artifacts"],
            "SWIFT_CONTAINERS",
        ),
    ],
)
def test_render_rejects_invalid_swift_settings(
    template: str,
    auth_secret: str,
    swift_base_url: str,
    containers: list[str],
    message: str,
) -> None:
    """Reject Swift values that cannot safely be interpolated into nginx."""
    with pytest.raises(ValueError, match=message):
        render_nginx_config(
            template,
            port=30000,
            swift_proxy_enabled=True,
            auth_secret=auth_secret,
            swift_base_url=swift_base_url,
            containers=containers,
        )


@pytest.mark.parametrize(
    ("port", "message"),
    [
        (70000, "listen port must be between"),
        (30001, "API port"),
        (9090, "metrics port"),
    ],
)
def test_render_rejects_invalid_or_reserved_port(template: str, port: int, message: str) -> None:
    """Reject listener ports that are invalid or already used by backend services."""
    with pytest.raises(ValueError, match=message):
        render_nginx_config(template, port=port, swift_proxy_enabled=False)


@pytest.mark.parametrize(
    "auth_url",
    [
        "http://keystone.example/v3",
        "https://user:password@keystone.example/v3",
        "https://keystone.example:70000/v3",
    ],
)
def test_validate_keystone_auth_url_rejects_unsafe_urls(auth_url: str) -> None:
    """Reject insecure or malformed Keystone endpoints."""
    with pytest.raises(ValueError, match="OS_AUTH_URL"):
        validate_keystone_auth_url(auth_url)


def test_validate_keystone_auth_url_accepts_https_url() -> None:
    """Accept normal HTTPS Keystone endpoints."""
    validate_keystone_auth_url("https://keystone.example:5000/v3")
