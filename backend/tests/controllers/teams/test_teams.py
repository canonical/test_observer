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


from fastapi.testclient import TestClient

from test_observer.common.permissions import Permission
from test_observer.data_access.models_enums import FamilyName
from tests.conftest import make_authenticated_request
from tests.data_generator import DataGenerator


def test_create_team(test_client: TestClient):
    response = make_authenticated_request(
        lambda: test_client.post(
            "/v1/teams",
            json={"name": "new-team"},
        ),
        Permission.change_team,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "new-team"
    assert data["permissions"] == []
    assert data["artefact_matching_rules"] == []
    assert data["members"] == []
    assert "id" in data


def test_create_team_with_permissions_and_matching_rules(test_client: TestClient):
    response = make_authenticated_request(
        lambda: test_client.post(
            "/v1/teams",
            json={
                "name": "test-team",
                "permissions": [Permission.view_user, Permission.change_team],
                "artefact_matching_rules": [
                    {"family": "snap"},
                    {"family": "deb"},
                ],
            },
        ),
        Permission.change_team,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-team"
    assert data["permissions"] == [Permission.view_user, Permission.change_team]
    assert len(data["artefact_matching_rules"]) == 2
    assert data["artefact_matching_rules"][0]["family"] == "snap"
    assert data["artefact_matching_rules"][0]["stage"] is None
    assert data["artefact_matching_rules"][0]["track"] is None
    assert data["artefact_matching_rules"][0]["branch"] is None
    assert data["artefact_matching_rules"][1]["family"] == "deb"
    assert data["members"] == []


def test_create_team_invalid_permission(test_client: TestClient):
    response = make_authenticated_request(
        lambda: test_client.post(
            "/v1/teams",
            json={
                "name": "test-team",
                "permissions": ["invalid_permission"],
            },
        ),
        Permission.change_team,
    )

    assert response.status_code == 422


def test_create_team_missing_name(test_client: TestClient):
    response = make_authenticated_request(
        lambda: test_client.post(
            "/v1/teams",
            json={},
        ),
        Permission.change_team,
    )

    assert response.status_code == 422


def test_create_team_duplicate_name(test_client: TestClient, generator: DataGenerator):
    generator.gen_team(name="existing-team")

    response = make_authenticated_request(
        lambda: test_client.post(
            "/v1/teams",
            json={"name": "existing-team"},
        ),
        Permission.change_team,
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_get_teams(test_client: TestClient, generator: DataGenerator):
    user = generator.gen_user()
    team = generator.gen_team(members=[user])

    response = make_authenticated_request(
        lambda: test_client.get("/v1/teams"), Permission.view_team
    )

    assert response.status_code == 200
    teams = response.json()
    assert len(teams) == 1
    assert teams[0]["id"] == team.id
    assert teams[0]["name"] == team.name
    assert teams[0]["permissions"] == team.permissions
    assert teams[0]["artefact_matching_rules"] == []
    assert len(teams[0]["members"]) == 1
    assert teams[0]["members"][0]["id"] == user.id


def test_get_team(test_client: TestClient, generator: DataGenerator):
    user = generator.gen_user()
    team = generator.gen_team(permissions=["create_artefact"], members=[user])

    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/teams/{team.id}"), Permission.view_team
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == team.id
    assert data["name"] == team.name
    assert data["permissions"] == team.permissions
    assert data["artefact_matching_rules"] == []
    assert len(data["members"]) == 1
    assert data["members"][0]["id"] == user.id


def test_update_team_permissions(test_client: TestClient, generator: DataGenerator):
    user = generator.gen_user()
    team = generator.gen_team(members=[user])

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/teams/{team.id}",
            json={"permissions": [Permission.view_user]},
        ),
        Permission.change_team,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == team.id
    assert data["name"] == team.name
    assert data["permissions"] == [Permission.view_user]
    assert data["artefact_matching_rules"] == []
    assert len(data["members"]) == 1
    assert data["members"][0]["id"] == user.id


def test_set_invalid_permission(test_client: TestClient, generator: DataGenerator):
    user = generator.gen_user()
    team = generator.gen_team(members=[user])

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/teams/{team.id}",
            json={"permissions": ["invalid_permission"]},
        ),
        Permission.change_team,
    )

    assert response.status_code == 422


def test_update_team_artefact_matching_rules(
    test_client: TestClient, generator: DataGenerator
):
    user = generator.gen_user()
    team = generator.gen_team(members=[user])

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/teams/{team.id}",
            json={
                "artefact_matching_rules": [
                    {"family": "snap"},
                    {"family": "deb", "stage": "proposed"},
                ]
            },
        ),
        Permission.change_team,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["artefact_matching_rules"]) == 2
    assert data["artefact_matching_rules"][0]["family"] == "snap"
    assert data["artefact_matching_rules"][0]["stage"] is None
    assert data["artefact_matching_rules"][1]["family"] == "deb"
    assert data["artefact_matching_rules"][1]["stage"] == "proposed"


def test_add_team_member(test_client: TestClient, generator: DataGenerator):
    team = generator.gen_team()
    user = generator.gen_user()

    response = make_authenticated_request(
        lambda: test_client.post(f"/v1/teams/{team.id}/members/{user.id}"),
        Permission.change_team,
    )

    assert response.status_code == 200
    assert len(response.json()["members"]) == 1
    assert response.json()["members"][0]["id"] == user.id


def test_add_team_member_idempotent(test_client: TestClient, generator: DataGenerator):
    user = generator.gen_user()
    team = generator.gen_team(members=[user])

    response = make_authenticated_request(
        lambda: test_client.post(f"/v1/teams/{team.id}/members/{user.id}"),
        Permission.change_team,
    )

    assert response.status_code == 200
    assert len(response.json()["members"]) == 1
    assert response.json()["members"][0]["id"] == user.id


def test_add_team_member_not_found(test_client: TestClient, generator: DataGenerator):
    team = generator.gen_team()
    user = generator.gen_user()

    # Test non-existent user
    response = make_authenticated_request(
        lambda: test_client.post(f"/v1/teams/{team.id}/members/999999"),
        Permission.change_team,
    )
    assert response.status_code == 404

    # Test non-existent team
    response = make_authenticated_request(
        lambda: test_client.post(f"/v1/teams/999999/members/{user.id}"),
        Permission.change_team,
    )
    assert response.status_code == 404


def test_remove_team_member(test_client: TestClient, generator: DataGenerator):
    user = generator.gen_user()
    team = generator.gen_team(members=[user])

    response = make_authenticated_request(
        lambda: test_client.delete(f"/v1/teams/{team.id}/members/{user.id}"),
        Permission.change_team,
    )

    assert response.status_code == 200
    assert response.json()["members"] == []


def test_remove_team_member_not_member(
    test_client: TestClient, generator: DataGenerator
):
    team = generator.gen_team()
    user = generator.gen_user()

    response = make_authenticated_request(
        lambda: test_client.delete(f"/v1/teams/{team.id}/members/{user.id}"),
        Permission.change_team,
    )

    assert response.status_code == 200
    assert response.json()["members"] == []


def test_remove_team_member_not_found(
    test_client: TestClient, generator: DataGenerator
):
    team = generator.gen_team()
    user = generator.gen_user()

    # Test non-existent user
    response = make_authenticated_request(
        lambda: test_client.delete(f"/v1/teams/{team.id}/members/999999"),
        Permission.change_team,
    )
    assert response.status_code == 404

    # Test non-existent team
    response = make_authenticated_request(
        lambda: test_client.delete(f"/v1/teams/999999/members/{user.id}"),
        Permission.change_team,
    )
    assert response.status_code == 404
