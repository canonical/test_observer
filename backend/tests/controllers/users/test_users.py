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
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import itsdangerous
import json

from test_observer.common.config import SESSIONS_SECRET
from test_observer.common.permissions import Permission
from test_observer.data_access.models_enums import FamilyName
from tests.conftest import make_authenticated_request
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


def test_get_users_response_format(test_client: TestClient, generator: DataGenerator):
    """Test that the GET /users endpoint returns proper response format"""
    team = generator.gen_team()
    user = generator.gen_user(teams=[team])

    response = make_authenticated_request(
        lambda: test_client.get("/v1/users"), Permission.view_user
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "users" in data
    assert "count" in data
    assert isinstance(data["users"], list)
    assert isinstance(data["count"], int)
    assert data["count"] >= 1

    # Verify user structure
    user_data = next((u for u in data["users"] if u["id"] == user.id), None)
    assert user_data is not None
    assert user_data["name"] == user.name
    assert user_data["email"] == user.email
    assert user_data["launchpad_handle"] == user.launchpad_handle
    assert user_data["is_admin"] == user.is_admin
    assert len(user_data["teams"]) == 1
    assert user_data["teams"][0]["id"] == team.id


def test_get_users_default_limit(test_client: TestClient, generator: DataGenerator):
    """Test that default limit is 50 users"""
    # Create 60 users
    for i in range(60):
        generator.gen_user(name=f"User {i:03d}", email=f"user{i:03d}@example.com")

    response = make_authenticated_request(
        lambda: test_client.get("/v1/users"), Permission.view_user
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 50
    assert data["count"] >= 60


def test_get_users_with_limit_and_offset(
    test_client: TestClient, generator: DataGenerator
):
    """Test pagination with explicit limit and offset"""
    # Create users with predictable names
    created_users = []
    for i in range(20):
        user = generator.gen_user(
            name=f"Test User {i:03d}", email=f"testuser{i:03d}@example.com"
        )
        created_users.append(user)

    # Sort by name to match the endpoint's ordering
    expected_names = sorted([u.name for u in created_users])

    # Get first page
    response = make_authenticated_request(
        lambda: test_client.get("/v1/users", params={"limit": 5, "offset": 0}),
        Permission.view_user,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 5
    returned_names = [u["name"] for u in data["users"]]
    assert returned_names == expected_names[:5]

    # Get second page
    response = make_authenticated_request(
        lambda: test_client.get("/v1/users", params={"limit": 5, "offset": 5}),
        Permission.view_user,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 5
    returned_names = [u["name"] for u in data["users"]]
    assert returned_names == expected_names[5:10]


def test_get_users_search_by_name(test_client: TestClient, generator: DataGenerator):
    """Test search filter by user name"""
    generator.gen_user(name="Alice Smith", email="alice@example.com")
    generator.gen_user(name="Bob Jones", email="bob@example.com")
    generator.gen_user(name="Charlie Brown", email="charlie@example.com")

    response = make_authenticated_request(
        lambda: test_client.get("/v1/users", params={"q": "Alice"}),
        Permission.view_user,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["users"][0]["name"] == "Alice Smith"


def test_get_users_search_by_email(test_client: TestClient, generator: DataGenerator):
    """Test search filter by user email"""
    generator.gen_user(name="User One", email="unique.email@example.com")
    generator.gen_user(name="User Two", email="another@example.com")

    response = make_authenticated_request(
        lambda: test_client.get("/v1/users", params={"q": "unique.email"}),
        Permission.view_user,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["users"][0]["email"] == "unique.email@example.com"


def test_get_users_search_by_launchpad_handle(
    test_client: TestClient, generator: DataGenerator
):
    """Test search filter by launchpad handle"""
    generator.gen_user(
        name="User One", email="user1@example.com", launchpad_handle="lp-user-one"
    )
    generator.gen_user(
        name="User Two", email="user2@example.com", launchpad_handle="lp-user-two"
    )

    response = make_authenticated_request(
        lambda: test_client.get("/v1/users", params={"q": "lp-user-one"}),
        Permission.view_user,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["users"][0]["launchpad_handle"] == "lp-user-one"


def test_get_users_search_by_id(test_client: TestClient, generator: DataGenerator):
    """Test search filter by user ID"""
    user1 = generator.gen_user(name="User One", email="user1@example.com")
    generator.gen_user(name="User Two", email="user2@example.com")

    response = make_authenticated_request(
        lambda: test_client.get("/v1/users", params={"q": str(user1.id)}),
        Permission.view_user,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["users"][0]["id"] == user1.id


def test_get_users_search_case_insensitive(
    test_client: TestClient, generator: DataGenerator
):
    """Test that search is case-insensitive"""
    generator.gen_user(name="CaseSensitive User", email="case@example.com")

    # Search with lowercase
    response = make_authenticated_request(
        lambda: test_client.get("/v1/users", params={"q": "casesensitive"}),
        Permission.view_user,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["users"][0]["name"] == "CaseSensitive User"


def test_get_users_search_partial_match(
    test_client: TestClient, generator: DataGenerator
):
    """Test that search supports partial matching"""
    generator.gen_user(name="Development User", email="dev@example.com")
    generator.gen_user(name="Production User", email="prod@example.com")

    response = make_authenticated_request(
        lambda: test_client.get("/v1/users", params={"q": "dev"}),
        Permission.view_user,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert "Development" in data["users"][0]["name"]


def test_get_users_search_multiple_terms(
    test_client: TestClient, generator: DataGenerator
):
    """Test search with multiple whitespace-separated terms (AND logic)"""
    generator.gen_user(name="John Smith", email="john.smith@example.com")
    generator.gen_user(name="John Doe", email="john.doe@example.com")
    generator.gen_user(name="Jane Smith", email="jane.smith@example.com")

    # Search for "John Smith" - should match only user with both terms
    response = make_authenticated_request(
        lambda: test_client.get("/v1/users", params={"q": "John Smith"}),
        Permission.view_user,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["users"][0]["name"] == "John Smith"


def test_get_users_search_with_pagination(
    test_client: TestClient, generator: DataGenerator
):
    """Test that search works with pagination"""
    # Create multiple users matching search
    for i in range(10):
        generator.gen_user(
            name=f"Search User {i:02d}", email=f"search{i:02d}@example.com"
        )

    response = make_authenticated_request(
        lambda: test_client.get(
            "/v1/users", params={"q": "Search", "limit": 3, "offset": 0}
        ),
        Permission.view_user,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 3
    assert data["count"] == 10


def test_get_users_pagination_limits(test_client: TestClient):
    """Test pagination parameter validation"""
    # Test maximum limit
    response = make_authenticated_request(
        lambda: test_client.get("/v1/users", params={"limit": 1001}),
        Permission.view_user,
    )
    assert response.status_code == 422

    # Test minimum limit
    response = make_authenticated_request(
        lambda: test_client.get("/v1/users", params={"limit": 0}),
        Permission.view_user,
    )
    assert response.status_code == 422

    # Test negative offset
    response = make_authenticated_request(
        lambda: test_client.get("/v1/users", params={"offset": -1}),
        Permission.view_user,
    )
    assert response.status_code == 422


def test_get_users_ordered_by_name(test_client: TestClient, generator: DataGenerator):
    """Test that users are ordered by name"""
    generator.gen_user(name="Zebra User", email="z@example.com")
    generator.gen_user(name="Alpha User", email="a@example.com")
    generator.gen_user(name="Middle User", email="m@example.com")

    response = make_authenticated_request(
        lambda: test_client.get("/v1/users"), Permission.view_user
    )

    assert response.status_code == 200
    data = response.json()

    # Find our test users in the response
    test_users = [
        u
        for u in data["users"]
        if u["email"] in ["z@example.com", "a@example.com", "m@example.com"]
    ]

    assert len(test_users) == 3
    assert test_users[0]["name"] == "Alpha User"
    assert test_users[1]["name"] == "Middle User"
    assert test_users[2]["name"] == "Zebra User"


def test_get_user(test_client: TestClient, generator: DataGenerator):
    team = generator.gen_team()
    user = generator.gen_user(teams=[team])

    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/users/{user.id}"), Permission.view_user
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "launchpad_handle": user.launchpad_handle,
        "is_admin": user.is_admin,
        "teams": [
            {
                "id": team.id,
                "name": team.name,
                "permissions": team.permissions,
                "artefact_matching_rules": team.artefact_matching_rules,
            }
        ],
    }


def test_set_user_as_reviewer(
    test_client: TestClient, generator: DataGenerator, db_session: Session
):
    snap_rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
    deb_rule = generator.gen_artefact_matching_rule(family=FamilyName.deb)
    
    team = generator.gen_team(artefact_matching_rules=[snap_rule, deb_rule])
    user = generator.gen_user(teams=[team])

    # Now user can review through their team
    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/users/{user.id}"),
        Permission.view_user,
    )

    assert response.status_code == 200
    # Verify user is part of the team
    assert len(response.json()["teams"]) == 1
    assert response.json()["teams"][0]["id"] == team.id
    db_session.refresh(user)
    assert user.teams == [team]


def test_promote_user_to_admin(
    test_client: TestClient, generator: DataGenerator, db_session: Session
):
    user = generator.gen_user()
    assert not user.is_admin

    response = make_authenticated_request(
        lambda: test_client.patch(f"/v1/users/{user.id}", json={"is_admin": True}),
        Permission.change_user,
    )

    assert response.status_code == 200
    db_session.refresh(user)
    assert user.is_admin
