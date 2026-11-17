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
from sqlalchemy.orm import Session

from test_observer.common import permissions
from test_observer.common.enums import Permission
from test_observer.data_access.models import Family
from tests.conftest import authenticate_user
from tests.data_generator import DataGenerator


@pytest.fixture
def admin_client(
    test_client: TestClient,
    generator: DataGenerator,
    create_session_cookie: Callable[[int], str],
) -> TestClient:
    user = generator.gen_user()
    user.is_admin = True
    authenticate_user(test_client, user, generator, create_session_cookie)
    test_client.headers["X-CSRF-Token"] = "1"
    return test_client


def test_list_seeded_families(test_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(permissions, "REQUIRE_AUTHENTICATION", False)

    response = test_client.get("/v1/families")

    assert response.status_code == 200
    assert response.json() == [{"name": name} for name in ("charm", "deb", "image", "snap", "solution")]


def test_list_families_requires_authentication(
    test_client: TestClient, generator: DataGenerator, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(permissions, "REQUIRE_AUTHENTICATION", True)
    assert test_client.get("/v1/families").status_code == 401

    application = generator.gen_application()
    response = test_client.get("/v1/families", headers={"Authorization": f"Bearer {application.api_key}"})
    assert response.status_code == 200


@pytest.mark.parametrize("name", ["NewFamily42", "New-Family42", "7", "a" * 100])
def test_admin_creates_family(admin_client: TestClient, db_session: Session, name: str) -> None:
    response = admin_client.post("/v1/families", json={"name": name})

    assert response.status_code == 201
    assert response.json() == {"name": name}
    assert db_session.get(Family, name) is not None
    assert {"name": name} in admin_client.get("/v1/families").json()


def test_duplicate_family(admin_client: TestClient) -> None:
    response = admin_client.post("/v1/families", json={"name": "snap"})

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": None},
        {"name": ""},
        {"name": "a" * 101},
        {"name": "two words"},
        {"name": "a_b"},
        {"name": "caf\u00e9"},
        {"name": "abc\n"},
    ],
)
def test_invalid_family_name(admin_client: TestClient, payload: dict) -> None:
    response = admin_client.post("/v1/families", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize("principal, expected_status", [("anonymous", 401), ("user", 403), ("application", 403)])
def test_only_admins_can_create_families_even_with_ignored_permissions(
    test_client: TestClient,
    generator: DataGenerator,
    create_session_cookie: Callable[[int], str],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    principal: str,
    expected_status: int,
) -> None:
    monkeypatch.setattr(permissions, "IGNORE_PERMISSIONS", set(Permission))
    monkeypatch.setattr(permissions, "REQUIRE_AUTHENTICATION", False)
    if principal == "user":
        team = generator.gen_team(permissions=list(Permission))
        user = generator.gen_user(teams=[team])
        authenticate_user(test_client, user, generator, create_session_cookie)
        test_client.headers["X-CSRF-Token"] = "1"
    elif principal == "application":
        application = generator.gen_application(permissions=list(Permission))
        test_client.headers["Authorization"] = f"Bearer {application.api_key}"

    response = test_client.post("/v1/families", json={"name": "Blocked"})

    assert response.status_code == expected_status
    assert db_session.get(Family, "Blocked") is None


def test_admin_session_requires_csrf_header(admin_client: TestClient) -> None:
    del admin_client.headers["X-CSRF-Token"]

    assert admin_client.post("/v1/families", json={"name": "Blocked"}).status_code == 401
