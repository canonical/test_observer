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

from collections.abc import Callable, Generator
from typing import Protocol

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from test_observer.common.permissions import requires_authentication
from test_observer.data_access.setup import get_db
from test_observer.main import app
from tests.conftest import authenticate_user
from tests.data_generator import DataGenerator


class MakeClientProtocol(Protocol):
    def __call__(self, local: bool, requires_auth: bool = True) -> TestClient: ...


@pytest.fixture
def make_client(db_session: Session) -> Generator[MakeClientProtocol, None, None]:
    initial_requires_auth_override = app.dependency_overrides.pop(requires_authentication, None)
    initial_get_db_override = app.dependency_overrides.pop(get_db, None)

    def _make_client(local: bool, requires_auth: bool = True) -> TestClient:
        app.dependency_overrides[requires_authentication] = lambda: requires_auth
        app.dependency_overrides[get_db] = lambda: db_session

        client = ("127.0.0.1", 12345) if local else ("123.45.67.89", 12345)
        return TestClient(app, client=client)

    yield _make_client

    # Clear any dependency overrides set by the test
    app.dependency_overrides.pop(requires_authentication, None)
    app.dependency_overrides.pop(get_db, None)
    # Restore the initial overrides if there were any
    if initial_requires_auth_override is not None:
        app.dependency_overrides[requires_authentication] = initial_requires_auth_override
    if initial_get_db_override is not None:
        app.dependency_overrides[get_db] = initial_get_db_override


def test_version_local_unauthenticated_with_auth_required(make_client: MakeClientProtocol):
    """Test that local unauthenticated access is allowed even when authentication is required"""
    response = make_client(local=True, requires_auth=True).get("/v1/version")
    assert response.status_code == 200
    assert "version" in response.json()


def test_version_local_unauthenticated_with_auth_not_required(
    make_client: MakeClientProtocol,
):
    """Test that local unauthenticated access is allowed when authentication is not required"""
    response = make_client(local=True, requires_auth=False).get("/v1/version")
    assert response.status_code == 200
    assert "version" in response.json()


def test_version_remote_unauthenticated_with_auth_required(make_client: MakeClientProtocol):
    """Test that remote unauthenticated access is denied when authentication is required"""
    response = make_client(local=False, requires_auth=True).get("/v1/version")
    assert response.status_code == 401


def test_version_remote_unauthenticated_with_auth_not_required(make_client: MakeClientProtocol):
    """Test that remote unauthenticated access is allowed when authentication is not required"""
    response = make_client(local=False, requires_auth=False).get("/v1/version")
    assert response.status_code == 200
    assert "version" in response.json()


def test_version_remote_authenticated_with_app(make_client: MakeClientProtocol, generator: DataGenerator):
    """Test that remote authenticated access with an application credential is allowed"""
    client = make_client(local=False, requires_auth=True)
    application = generator.gen_application(permissions=[])
    response = client.get("/v1/version", headers={"Authorization": f"Bearer {application.api_key}"})
    assert response.status_code == 200
    assert "version" in response.json()


def test_version_remote_authenticated_with_user(
    make_client: MakeClientProtocol,
    generator: DataGenerator,
    create_session_cookie: Callable[[int], str],
):
    """Test that remote authenticated access with user credentials is allowed"""
    client = make_client(local=False, requires_auth=True)
    user = generator.gen_user()
    authenticate_user(client, user, generator, create_session_cookie)
    response = client.get("/v1/version", headers={"X-CSRF-Token": "1"})
    assert response.status_code == 200
    assert "version" in response.json()
