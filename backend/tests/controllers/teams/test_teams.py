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
import pytest
from sqlalchemy.exc import IntegrityError

from test_observer.common.permissions import Permission
from test_observer.data_access.models import ArtefactMatchingRule
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


def test_create_team_with_complex_matching_rules(test_client: TestClient):
    """Test creating a team with matching rules including track and branch"""
    response = make_authenticated_request(
        lambda: test_client.post(
            "/v1/teams",
            json={
                "name": "complex-rules-team",
                "artefact_matching_rules": [
                    {"family": "snap", "track": "22"},
                    {"family": "snap", "track": "24", "stage": "beta"},
                    {"family": "deb", "branch": "jammy"},
                    {
                        "family": "charm",
                        "track": "1.0",
                        "stage": "edge",
                        "branch": "feature-x",
                    },
                ],
            },
        ),
        Permission.change_team,
    )

    assert response.status_code == 201
    data = response.json()
    assert len(data["artefact_matching_rules"]) == 4

    # Check snap with track only
    snap_track = next(
        r for r in data["artefact_matching_rules"] if r["track"] == "22"
    )
    assert snap_track["family"] == "snap"
    assert snap_track["stage"] is None
    assert snap_track["branch"] is None

    # Check snap with track and stage
    snap_track_stage = next(
        r for r in data["artefact_matching_rules"] if r["track"] == "24"
    )
    assert snap_track_stage["family"] == "snap"
    assert snap_track_stage["stage"] == "beta"
    assert snap_track_stage["branch"] is None

    # Check deb with branch
    deb_branch = next(
        r for r in data["artefact_matching_rules"] if r["family"] == "deb"
    )
    assert deb_branch["branch"] == "jammy"
    assert deb_branch["stage"] is None
    assert deb_branch["track"] is None

    # Check charm with all fields
    charm_full = next(
        r for r in data["artefact_matching_rules"] if r["family"] == "charm"
    )
    assert charm_full["track"] == "1.0"
    assert charm_full["stage"] == "edge"
    assert charm_full["branch"] == "feature-x"


def test_update_team_replaces_matching_rules(
    test_client: TestClient, generator: DataGenerator
):
    """Test that updating matching rules replaces existing ones"""
    # Create a team with initial rules
    snap_rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
    deb_rule = generator.gen_artefact_matching_rule(family=FamilyName.deb)
    team = generator.gen_team(artefact_matching_rules=[snap_rule, deb_rule])

    assert len(team.artefact_matching_rules) == 2

    # Update with new rules
    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/teams/{team.id}",
            json={
                "artefact_matching_rules": [
                    {"family": "charm", "track": "stable"},
                    {"family": "image"},
                ]
            },
        ),
        Permission.change_team,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["artefact_matching_rules"]) == 2

    # Verify old rules are gone and new ones are present
    families = [r["family"] for r in data["artefact_matching_rules"]]
    assert "charm" in families
    assert "image" in families
    assert "snap" not in families
    assert "deb" not in families

    # Verify charm rule has track
    charm_rule = next(r for r in data["artefact_matching_rules"] if r["family"] == "charm")
    assert charm_rule["track"] == "stable"


def test_update_team_clears_matching_rules(
    test_client: TestClient, generator: DataGenerator
):
    """Test that setting matching rules to empty array clears all rules"""
    snap_rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
    deb_rule = generator.gen_artefact_matching_rule(family=FamilyName.deb)
    team = generator.gen_team(artefact_matching_rules=[snap_rule, deb_rule])

    assert len(team.artefact_matching_rules) == 2

    # Clear all rules
    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/teams/{team.id}",
            json={"artefact_matching_rules": []},
        ),
        Permission.change_team,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["artefact_matching_rules"]) == 0


def test_update_team_matching_rules_reuses_existing(
    test_client: TestClient, generator: DataGenerator
):
    """Test that identical matching rules are reused across teams"""
    # Create a rule and assign it to team1
    snap_rule = generator.gen_artefact_matching_rule(
        family=FamilyName.snap, track="22"
    )
    team1 = generator.gen_team(name="team1", artefact_matching_rules=[snap_rule])

    # Create team2 with the same rule
    response = make_authenticated_request(
        lambda: test_client.post(
            "/v1/teams",
            json={
                "name": "team2",
                "artefact_matching_rules": [{"family": "snap", "track": "22"}],
            },
        ),
        Permission.change_team,
    )

    assert response.status_code == 201
    data = response.json()
    assert len(data["artefact_matching_rules"]) == 1

    # Both teams should reference the same rule
    team1_rule_id = team1.artefact_matching_rules[0].id
    team2_rule_id = data["artefact_matching_rules"][0]["id"]
    assert team1_rule_id == team2_rule_id


def test_update_team_with_duplicate_matching_rules(
    test_client: TestClient, generator: DataGenerator
):
    """Test that providing duplicate rules in the request is handled"""
    team = generator.gen_team()

    # Try to create rules with duplicates
    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/teams/{team.id}",
            json={
                "artefact_matching_rules": [
                    {"family": "snap", "track": "22"},
                    {"family": "snap", "track": "22"},  # Duplicate
                ]
            },
        ),
        Permission.change_team,
    )

    # Should still succeed - duplicates are just ignored
    assert response.status_code == 200
    data = response.json()
    # Should only have one rule due to unique constraint
    assert len(data["artefact_matching_rules"]) == 1
    assert data["artefact_matching_rules"][0]["family"] == "snap"
    assert data["artefact_matching_rules"][0]["track"] == "22"


def test_get_team_returns_matching_rules(
    test_client: TestClient, generator: DataGenerator
):
    """Test that getting a team returns its matching rules"""
    snap_rule = generator.gen_artefact_matching_rule(
        family=FamilyName.snap, track="22", stage="stable"
    )
    deb_rule = generator.gen_artefact_matching_rule(
        family=FamilyName.deb, branch="jammy"
    )
    team = generator.gen_team(
        name="test-team", artefact_matching_rules=[snap_rule, deb_rule]
    )

    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/teams/{team.id}"), Permission.view_team
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["artefact_matching_rules"]) == 2

    snap = next(r for r in data["artefact_matching_rules"] if r["family"] == "snap")
    assert snap["track"] == "22"
    assert snap["stage"] == "stable"
    assert snap["branch"] is None

    deb = next(r for r in data["artefact_matching_rules"] if r["family"] == "deb")
    assert deb["branch"] == "jammy"
    assert deb["track"] is None
    assert deb["stage"] is None


def test_update_team_keeps_permissions_when_updating_rules(
    test_client: TestClient, generator: DataGenerator
):
    """Test that updating rules doesn't affect permissions"""
    team = generator.gen_team(permissions=["view_user", "change_team"])

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/teams/{team.id}",
            json={"artefact_matching_rules": [{"family": "snap"}]},
        ),
        Permission.change_team,
    )

    assert response.status_code == 200
    data = response.json()
    # Permissions should remain unchanged
    assert data["permissions"] == ["view_user", "change_team"]
    assert len(data["artefact_matching_rules"]) == 1


def test_database_allows_duplicate_rules_with_nulls(db_session):
    """
    Test that demonstrates PostgreSQL's NULL handling in unique constraints.
    PostgreSQL treats NULL values as distinct, so two rules with the same
    non-NULL values but NULL in other columns are considered different.
    This is why we need application-level deduplication in _sync_artefact_matching_rules.
    """
    rule1 = ArtefactMatchingRule(
        family=FamilyName.snap,
        stage=None,
        track="22",
        branch=None,
    )
    db_session.add(rule1)
    db_session.flush()
    
    rule2 = ArtefactMatchingRule(
        family=FamilyName.snap,
        stage=None,
        track="22",
        branch=None,
    )
    db_session.add(rule2)
    
    # PostgreSQL allows this because NULL != NULL in unique constraints
    db_session.flush()  # No IntegrityError is raised
    
    # Both rules were created
    assert rule1.id != rule2.id
