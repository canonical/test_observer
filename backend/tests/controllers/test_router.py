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

import pytest
from fastapi.testclient import TestClient

from test_observer.common.enums import Permission
from test_observer.common.permissions import requires_authentication
from test_observer.main import app
from tests.conftest import authenticate_user, make_authenticated_request
from tests.data_generator import DataGenerator


def test_base_unauthenticated_auth_not_required(test_client: TestClient):
    try:
        app.dependency_overrides[requires_authentication] = lambda: False
        response = test_client.get("/")
        assert response.status_code == 200
        assert response.text == '"test observer api"'
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_base_unauthenticated_auth_required(test_client: TestClient):
    try:
        app.dependency_overrides[requires_authentication] = lambda: True
        response = test_client.get("/")
        assert response.status_code == 401
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_base_authenticated_app_auth_not_required(test_client: TestClient, generator: DataGenerator):
    try:
        app.dependency_overrides[requires_authentication] = lambda: False
        application = generator.gen_application(permissions=[])
        response = test_client.get("/", headers={"Authorization": f"Bearer {application.api_key}"})
        assert response.status_code == 200
        assert response.text == '"test observer api"'
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_base_authenticated_user_auth_not_required(
    test_client: TestClient, generator: DataGenerator, create_session_cookie: Callable[[int], str]
):
    try:
        app.dependency_overrides[requires_authentication] = lambda: False
        user = generator.gen_user()
        authenticate_user(test_client, user, generator, create_session_cookie)
        response = test_client.get("/", headers={"X-CSRF-Token": "1"})
        assert response.status_code == 200
        assert response.text == '"test observer api"'
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_base_authenticated_app_auth_required(test_client: TestClient, generator: DataGenerator):
    try:
        app.dependency_overrides[requires_authentication] = lambda: True
        application = generator.gen_application(permissions=[])
        response = test_client.get("/", headers={"Authorization": f"Bearer {application.api_key}"})
        assert response.status_code == 200
        assert response.text == '"test observer api"'
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_base_authenticated_user_auth_required(
    test_client: TestClient, generator: DataGenerator, create_session_cookie: Callable[[int], str]
):
    try:
        app.dependency_overrides[requires_authentication] = lambda: True
        user = generator.gen_user()
        authenticate_user(test_client, user, generator, create_session_cookie)
        response = test_client.get("/", headers={"X-CSRF-Token": "1"})
        assert response.status_code == 200
        assert response.text == '"test observer api"'
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_sentry_debug_without_permission(test_client: TestClient):
    response = make_authenticated_request(
        lambda: test_client.get("/sentry-debug"),
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions"}


def test_sentry_debug_with_permission(test_client: TestClient):
    with pytest.raises(ZeroDivisionError):
        make_authenticated_request(
            lambda: test_client.get("/sentry-debug"),
            Permission.view_sentry_debug,
        )
