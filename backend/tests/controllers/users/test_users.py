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


from base64 import b64encode
from datetime import datetime, timedelta
import json

import itsdangerous
from fastapi.testclient import TestClient

from test_observer.common.config import SESSIONS_SECRET
from tests.data_generator import DataGenerator


def _create_session_cookie(session_id: int) -> str:
    """Create a signed session cookie for testing"""
    signer = itsdangerous.TimestampSigner(str(SESSIONS_SECRET))
    session_data = {"id": session_id}
    session_json = json.dumps(session_data)
    return signer.sign(b64encode(session_json.encode()).decode()).decode()


def test_get_me_without_csrf_token_returns_none(
    test_client: TestClient, generator: DataGenerator
):
    """Test that accessing /me without X-CSRF-Token header returns None"""
    user = generator.gen_user()
    session = generator.gen_user_session(user)

    session_cookie = _create_session_cookie(session.id)
    test_client.cookies.set("session", session_cookie)

    response = test_client.get("/v1/users/me")

    assert response.status_code == 200
    assert response.json() is None


def test_get_me_without_session_returns_none(test_client: TestClient):
    response = test_client.get("/v1/users/me", headers={"X-CSRF-Token": "1"})

    assert response.status_code == 200
    assert response.json() is None


def test_get_me_with_expired_session_returns_none(
    test_client: TestClient, generator: DataGenerator
):
    user = generator.gen_user()
    session = generator.gen_user_session(
        user, expires_at=datetime.now() - timedelta(days=1)
    )

    session_cookie = _create_session_cookie(session.id)
    test_client.cookies.set("session", session_cookie)

    response = test_client.get("/v1/users/me", headers={"X-CSRF-Token": "1"})

    assert response.status_code == 200
    assert response.json() is None


def test_get_me_with_nonexistent_session_returns_none(test_client: TestClient):
    session_cookie = _create_session_cookie(999999)  # Non-existent session ID
    test_client.cookies.set("session", session_cookie)

    response = test_client.get("/v1/users/me", headers={"X-CSRF-Token": "1"})

    assert response.status_code == 200
    assert response.json() is None


def test_get_me_with_valid_session_returns_user_data(
    test_client: TestClient, generator: DataGenerator
):
    user = generator.gen_user()
    session = generator.gen_user_session(user)

    session_cookie = _create_session_cookie(session.id)
    test_client.cookies.set("session", session_cookie)

    response = test_client.get("/v1/users/me", headers={"X-CSRF-Token": "1"})

    assert response.status_code == 200
    user_data = response.json()
    assert user_data is not None
    assert user_data["id"] == user.id
    assert user_data["name"] == user.name
    assert user_data["email"] == user.email
    assert user_data["launchpad_handle"] == user.launchpad_handle


def test_get_users(test_client: TestClient, generator: DataGenerator):
    team = generator.gen_team()
    user = generator.gen_user(teams=[team])

    response = test_client.get("/v1/users")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "launchpad_handle": user.launchpad_handle,
            "is_reviewer": user.is_reviewer,
            "teams": [
                {
                    "id": team.id,
                    "name": team.name,
                    "permissions": team.permissions,
                }
            ],
        }
    ]


def test_get_user(test_client: TestClient, generator: DataGenerator):
    team = generator.gen_team()
    user = generator.gen_user(teams=[team])

    response = test_client.get(f"/v1/users/{user.id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "launchpad_handle": user.launchpad_handle,
        "is_reviewer": user.is_reviewer,
        "teams": [
            {
                "id": team.id,
                "name": team.name,
                "permissions": team.permissions,
            }
        ],
    }
