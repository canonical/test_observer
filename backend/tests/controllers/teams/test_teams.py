# Copyright 2025 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

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
    assert data["reviewer_families"] == []
    assert data["members"] == []
    assert "id" in data


def test_create_team_with_permissions_and_families(test_client: TestClient):
    response = make_authenticated_request(
        lambda: test_client.post(
            "/v1/teams",
            json={
                "name": "test-team",
                "permissions": [Permission.view_user, Permission.change_team],
                "reviewer_families": ["snap", "deb"],
            },
        ),
        Permission.change_team,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-team"
    assert data["permissions"] == [Permission.view_user, Permission.change_team]
    assert data["reviewer_families"] == ["snap", "deb"]
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

    response = make_authenticated_request(lambda: test_client.get("/v1/teams"), Permission.view_team)

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": team.id,
            "name": team.name,
            "permissions": team.permissions,
            "reviewer_families": team.reviewer_families,
            "artefact_matching_rules": team.artefact_matching_rules,
            "members": [
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "launchpad_handle": user.launchpad_handle,
                    "is_admin": user.is_admin,
                }
            ],
        },
    ]


def test_get_team(test_client: TestClient, generator: DataGenerator):
    user = generator.gen_user()
    team = generator.gen_team(permissions=["create_artefact"], members=[user])

    response = make_authenticated_request(lambda: test_client.get(f"/v1/teams/{team.id}"), Permission.view_team)

    assert response.status_code == 200
    assert response.json() == {
        "id": team.id,
        "name": team.name,
        "permissions": team.permissions,
        "reviewer_families": team.reviewer_families,
        "artefact_matching_rules": team.artefact_matching_rules,
        "members": [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "launchpad_handle": user.launchpad_handle,
                "is_admin": user.is_admin,
            }
        ],
    }


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
    assert response.json() == {
        "id": team.id,
        "name": team.name,
        "permissions": [Permission.view_user],
        "reviewer_families": team.reviewer_families,
        "artefact_matching_rules": team.artefact_matching_rules,
        "members": [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "launchpad_handle": user.launchpad_handle,
                "is_admin": user.is_admin,
            }
        ],
    }


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


def test_update_team_reviewer_families(test_client: TestClient, generator: DataGenerator):
    user = generator.gen_user()
    team = generator.gen_team(members=[user])

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/teams/{team.id}",
            json={"reviewer_families": ["snap", "deb"]},
        ),
        Permission.change_team,
    )

    assert response.status_code == 200
    assert response.json()["reviewer_families"] == ["snap", "deb"]


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


def test_remove_team_member_not_member(test_client: TestClient, generator: DataGenerator):
    team = generator.gen_team()
    user = generator.gen_user()

    response = make_authenticated_request(
        lambda: test_client.delete(f"/v1/teams/{team.id}/members/{user.id}"),
        Permission.change_team,
    )

    assert response.status_code == 200
    assert response.json()["members"] == []


def test_remove_team_member_not_found(test_client: TestClient, generator: DataGenerator):
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


def test_remove_rule_from_team_making_it_an_orphan_removes_rule(
    test_client: TestClient, generator: DataGenerator
):
    team = generator.gen_team()
    rule = generator.gen_artefact_matching_rule(family=FamilyName.snap, teams=[team])

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/teams/{team.id}",
            json={"artefact_matching_rules": []},
        ),
        Permission.change_team,
    )

    assert response.status_code == 200
    assert response.json()["artefact_matching_rules"] == []
    # assert that rule is deleted
    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefact-matching-rules/{rule.id}"),
        Permission.view_team,
    )
    assert response.status_code == 404


def test_remove_rule_from_team_without_making_it_an_orphan_does_not_remove_rule(
    test_client: TestClient, generator: DataGenerator
):
    team = generator.gen_team(name="team1")
    other_team = generator.gen_team(name="team2")
    rule = generator.gen_artefact_matching_rule(family=FamilyName.snap, teams=[team, other_team])

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/teams/{team.id}",
            json={"artefact_matching_rules": []},
        ),
        Permission.change_team,
    )

    assert response.status_code == 200
    assert response.json()["artefact_matching_rules"] == []
    # assert that rule is deleted
    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefact-matching-rules/{rule.id}"),
        Permission.view_team,
    )
    assert response.status_code == 200
