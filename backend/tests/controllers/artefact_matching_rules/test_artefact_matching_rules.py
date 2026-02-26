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


def test_create_artefact_matching_rule(test_client: TestClient, generator: DataGenerator):
    """Test creating a new artefact matching rule with a team"""
    team = generator.gen_team(name="test-team")
    
    response = make_authenticated_request(
        lambda: test_client.post(
            "/v1/artefact-matching-rules",
            json={"family": "snap", "track": "22", "team_ids": [team.id]},
        ),
        Permission.change_team,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["family"] == "snap"
    assert data["track"] == "22"
    assert data["stage"] is None
    assert data["branch"] is None
    assert len(data["teams"]) == 1
    assert data["teams"][0]["id"] == team.id
    assert "id" in data


def test_create_artefact_matching_rule_all_fields(test_client: TestClient, generator: DataGenerator):
    """Test creating a rule with all fields populated"""
    team = generator.gen_team(name="test-team")
    
    response = make_authenticated_request(
        lambda: test_client.post(
            "/v1/artefact-matching-rules",
            json={
                "family": "snap",
                "track": "22",
                "stage": "beta",
                "branch": "hotfix",
                "team_ids": [team.id],
            },
        ),
        Permission.change_team,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["family"] == "snap"
    assert data["track"] == "22"
    assert data["stage"] == "beta"
    assert data["branch"] == "hotfix"
    assert len(data["teams"]) == 1


def test_create_artefact_matching_rule_family_only(test_client: TestClient, generator: DataGenerator):
    """Test creating a rule with only family"""
    team = generator.gen_team(name="test-team")
    
    response = make_authenticated_request(
        lambda: test_client.post(
            "/v1/artefact-matching-rules",
            json={"family": "deb", "team_ids": [team.id]},
        ),
        Permission.change_team,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["family"] == "deb"
    assert data["track"] is None
    assert data["stage"] is None
    assert data["branch"] is None
    assert len(data["teams"]) == 1


def test_create_artefact_matching_rule_without_teams(test_client: TestClient):
    """Test that creating a rule without teams fails"""
    response = make_authenticated_request(
        lambda: test_client.post(
            "/v1/artefact-matching-rules",
            json={"family": "snap", "track": "22", "team_ids": []},
        ),
        Permission.change_team,
    )

    assert response.status_code == 400
    assert "At least one team is required" in response.json()["detail"]


def test_create_artefact_matching_rule_with_nonexistent_team(test_client: TestClient):
    """Test that creating a rule with non-existent team fails"""
    response = make_authenticated_request(
        lambda: test_client.post(
            "/v1/artefact-matching-rules",
            json={"family": "snap", "track": "22", "team_ids": [999999]},
        ),
        Permission.change_team,
    )

    assert response.status_code == 404
    assert "doesn't exist" in response.json()["detail"]


def test_create_artefact_matching_rule_with_multiple_teams(
    test_client: TestClient, generator: DataGenerator
):
    """Test creating a rule with multiple teams"""
    team1 = generator.gen_team(name="team1")
    team2 = generator.gen_team(name="team2")
    
    response = make_authenticated_request(
        lambda: test_client.post(
            "/v1/artefact-matching-rules",
            json={
                "family": "snap",
                "track": "22",
                "team_ids": [team1.id, team2.id],
            },
        ),
        Permission.change_team,
    )

    assert response.status_code == 201
    data = response.json()
    assert len(data["teams"]) == 2
    team_ids = {t["id"] for t in data["teams"]}
    assert team_ids == {team1.id, team2.id}


def test_create_artefact_matching_rule_duplicate(
    test_client: TestClient, generator: DataGenerator
):
    """Test that creating a duplicate rule returns 409"""
    team = generator.gen_team(name="test-team")
    generator.gen_artefact_matching_rule(family=FamilyName.snap, track="22", teams=[team])

    response = make_authenticated_request(
        lambda: test_client.post(
            "/v1/artefact-matching-rules",
            json={"family": "snap", "track": "22", "team_ids": [team.id]},
        ),
        Permission.change_team,
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_artefact_matching_rule_invalid_family(test_client: TestClient, generator: DataGenerator):
    """Test that invalid family is rejected"""
    team = generator.gen_team(name="test-team")
    
    response = make_authenticated_request(
        lambda: test_client.post(
            "/v1/artefact-matching-rules",
            json={"family": "invalid", "team_ids": [team.id]},
        ),
        Permission.change_team,
    )

    assert response.status_code == 422


def test_get_artefact_matching_rules(test_client: TestClient, generator: DataGenerator):
    """Test getting all artefact matching rules"""
    rule1 = generator.gen_artefact_matching_rule(family=FamilyName.snap, track="22")
    rule2 = generator.gen_artefact_matching_rule(
        family=FamilyName.deb, stage="proposed"
    )

    response = make_authenticated_request(
        lambda: test_client.get("/v1/artefact-matching-rules"), Permission.view_team
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    rule_ids = [r["id"] for r in data]
    assert rule1.id in rule_ids
    assert rule2.id in rule_ids


def test_get_artefact_matching_rules_with_teams(
    test_client: TestClient, generator: DataGenerator
):
    """Test that getting rules includes team information"""
    team1 = generator.gen_team(name="team1")
    team2 = generator.gen_team(name="team2")
    rule = generator.gen_artefact_matching_rule(
        family=FamilyName.snap, track="22", teams=[team1, team2]
    )

    response = make_authenticated_request(
        lambda: test_client.get("/v1/artefact-matching-rules"), Permission.view_team
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1

    rule_data = data[0]
    assert rule_data["id"] == rule.id
    assert len(rule_data["teams"]) == 2
    team_names = [t["name"] for t in rule_data["teams"]]
    assert "team1" in team_names
    assert "team2" in team_names


def test_get_artefact_matching_rules_filtered_by_family(
    test_client: TestClient, generator: DataGenerator
):
    """Test filtering rules by family"""
    generator.gen_artefact_matching_rule(family=FamilyName.snap, track="22")
    generator.gen_artefact_matching_rule(family=FamilyName.snap, track="24")
    generator.gen_artefact_matching_rule(family=FamilyName.deb, stage="proposed")

    response = make_authenticated_request(
        lambda: test_client.get("/v1/artefact-matching-rules?family=snap"),
        Permission.view_team,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(r["family"] == "snap" for r in data)


def test_get_artefact_matching_rule_by_id(
    test_client: TestClient, generator: DataGenerator
):
    """Test getting a specific rule by ID"""
    rule = generator.gen_artefact_matching_rule(
        family=FamilyName.snap, track="22", stage="stable"
    )

    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefact-matching-rules/{rule.id}"),
        Permission.view_team,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == rule.id
    assert data["family"] == "snap"
    assert data["track"] == "22"
    assert data["stage"] == "stable"


def test_get_artefact_matching_rule_not_found(test_client: TestClient):
    """Test getting a non-existent rule"""
    response = make_authenticated_request(
        lambda: test_client.get("/v1/artefact-matching-rules/999999"),
        Permission.view_team,
    )

    assert response.status_code == 404


def test_update_artefact_matching_rule(
    test_client: TestClient, generator: DataGenerator
):
    """Test updating an artefact matching rule"""
    team = generator.gen_team(name="test-team")
    rule = generator.gen_artefact_matching_rule(family=FamilyName.snap, track="22", teams=[team])

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefact-matching-rules/{rule.id}",
            json={
                "family": "snap",
                "track": "24",
                "stage": "stable",
            },
        ),
        Permission.change_team,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == rule.id
    assert data["family"] == "snap"
    assert data["track"] == "24"
    assert data["stage"] == "stable"
    assert data["branch"] is None
    # Teams should be preserved
    assert len(data["teams"]) == 1
    assert data["teams"][0]["id"] == team.id


def test_update_artefact_matching_rule_change_family(
    test_client: TestClient, generator: DataGenerator
):
    """Test changing the family of a rule"""
    team = generator.gen_team(name="test-team")
    rule = generator.gen_artefact_matching_rule(family=FamilyName.snap, track="22", teams=[team])

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefact-matching-rules/{rule.id}",
            json={
                "family": "deb",
                "track": "22",
            },
        ),
        Permission.change_team,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["family"] == "deb"
    assert data["track"] == "22"


def test_update_artefact_matching_rule_change_teams(
    test_client: TestClient, generator: DataGenerator
):
    """Test changing the teams of a rule"""
    team1 = generator.gen_team(name="team1")
    team2 = generator.gen_team(name="team2")
    team3 = generator.gen_team(name="team3")
    rule = generator.gen_artefact_matching_rule(
        family=FamilyName.snap, track="22", teams=[team1, team2]
    )

    # Change to team3 only
    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefact-matching-rules/{rule.id}",
            json={
                "family": "snap",
                "team_ids": [team3.id],
            },
        ),
        Permission.change_team,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["teams"]) == 1
    assert data["teams"][0]["id"] == team3.id


def test_update_artefact_matching_rule_remove_all_teams(
    test_client: TestClient, generator: DataGenerator
):
    """Test that removing all teams fails"""
    team = generator.gen_team(name="test-team")
    rule = generator.gen_artefact_matching_rule(family=FamilyName.snap, track="22", teams=[team])

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefact-matching-rules/{rule.id}",
            json={
                "family": "snap",
                "team_ids": [],
            },
        ),
        Permission.change_team,
    )

    assert response.status_code == 400
    assert "At least one team is required" in response.json()["detail"]


def test_update_artefact_matching_rule_conflict(
    test_client: TestClient, generator: DataGenerator
):
    """Test that updating to duplicate values returns 409"""
    team = generator.gen_team(name="test-team")
    generator.gen_artefact_matching_rule(family=FamilyName.snap, track="22", teams=[team])
    rule2 = generator.gen_artefact_matching_rule(family=FamilyName.snap, track="24", teams=[team])

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefact-matching-rules/{rule2.id}",
            json={
                "family": "snap",
                "track": "22",
            },
        ),
        Permission.change_team,
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_update_artefact_matching_rule_not_found(test_client: TestClient, generator: DataGenerator):
    """Test updating a non-existent rule"""
    team = generator.gen_team(name="test-team")
    
    response = make_authenticated_request(
        lambda: test_client.patch(
            "/v1/artefact-matching-rules/999999",
            json={"family": "snap", "track": "22"},
        ),
        Permission.change_team,
    )

    assert response.status_code == 404


def test_update_artefact_matching_rule_preserves_teams(
    test_client: TestClient, generator: DataGenerator
):
    """Test that updating a rule without team_ids preserves team associations"""
    team1 = generator.gen_team(name="team1")
    team2 = generator.gen_team(name="team2")
    rule = generator.gen_artefact_matching_rule(
        family=FamilyName.snap, track="22", teams=[team1, team2]
    )

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefact-matching-rules/{rule.id}",
            json={
                "family": "snap",
                "track": "24",
            },
        ),
        Permission.change_team,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["teams"]) == 2
    team_names = [t["name"] for t in data["teams"]]
    assert "team1" in team_names
    assert "team2" in team_names


def test_delete_artefact_matching_rule(
    test_client: TestClient, generator: DataGenerator
):
    """Test deleting an artefact matching rule"""
    team = generator.gen_team(name="test-team")
    rule = generator.gen_artefact_matching_rule(family=FamilyName.snap, track="22", teams=[team])

    response = make_authenticated_request(
        lambda: test_client.delete(f"/v1/artefact-matching-rules/{rule.id}"),
        Permission.change_team,
    )

    assert response.status_code == 204

    # Verify rule is deleted
    get_response = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefact-matching-rules/{rule.id}"),
        Permission.view_team,
    )
    assert get_response.status_code == 404


def test_delete_artefact_matching_rule_with_teams(
    test_client: TestClient, generator: DataGenerator
):
    """Test deleting a rule removes it from teams"""
    team = generator.gen_team(name="test-team")
    rule = generator.gen_artefact_matching_rule(
        family=FamilyName.snap, track="22", teams=[team]
    )

    response = make_authenticated_request(
        lambda: test_client.delete(f"/v1/artefact-matching-rules/{rule.id}"),
        Permission.change_team,
    )

    assert response.status_code == 204

    # Verify team still exists
    team_response = make_authenticated_request(
        lambda: test_client.get(f"/v1/teams/{team.id}"),
        Permission.view_team,
    )
    assert team_response.status_code == 200
    # Team should have no matching rules now
    assert len(team_response.json()["artefact_matching_rules"]) == 0


def test_delete_artefact_matching_rule_not_found(test_client: TestClient):
    """Test deleting a non-existent rule"""
    response = make_authenticated_request(
        lambda: test_client.delete("/v1/artefact-matching-rules/999999"),
        Permission.change_team,
    )

    assert response.status_code == 404


def test_get_empty_artefact_matching_rules(test_client: TestClient):
    """Test getting rules when none exist"""
    response = make_authenticated_request(
        lambda: test_client.get("/v1/artefact-matching-rules"),
        Permission.view_team,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_permissions_required_for_create(test_client: TestClient, generator: DataGenerator):
    """Test that change_team permission is required to create rules"""
    team = generator.gen_team(name="test-team")
    
    response = test_client.post(
        "/v1/artefact-matching-rules",
        json={"family": "snap", "track": "22", "team_ids": [team.id]},
    )

    assert response.status_code == 403


def test_permissions_required_for_update(
    test_client: TestClient, generator: DataGenerator
):
    """Test that change_team permission is required to update rules"""
    team = generator.gen_team(name="test-team")
    rule = generator.gen_artefact_matching_rule(family=FamilyName.snap, track="22", teams=[team])

    response = test_client.patch(
        f"/v1/artefact-matching-rules/{rule.id}",
        json={"family": "snap", "track": "24"},
    )

    assert response.status_code == 403


def test_permissions_required_for_delete(
    test_client: TestClient, generator: DataGenerator
):
    """Test that change_team permission is required to delete rules"""
    team = generator.gen_team(name="test-team")
    rule = generator.gen_artefact_matching_rule(family=FamilyName.snap, track="22", teams=[team])

    response = test_client.delete(f"/v1/artefact-matching-rules/{rule.id}")

    assert response.status_code == 403


def test_permissions_required_for_view(test_client: TestClient):
    """Test that view_team permission is required to view rules"""
    response = test_client.get("/v1/artefact-matching-rules")

    assert response.status_code == 403


def test_integration_with_teams_api(test_client: TestClient, generator: DataGenerator):
    """Test that rules created via rules API appear in teams API"""
    # Create a team
    team = generator.gen_team(name="test-team")
    
    # Create a rule via the rules API with the team
    rule_response = make_authenticated_request(
        lambda: test_client.post(
            "/v1/artefact-matching-rules",
            json={"family": "snap", "track": "22", "team_ids": [team.id]},
        ),
        Permission.change_team,
    )
    assert rule_response.status_code == 201
    rule_id = rule_response.json()["id"]

    # Verify the rule appears in the team via teams API
    team_response = make_authenticated_request(
        lambda: test_client.get(f"/v1/teams/{team.id}"),
        Permission.view_team,
    )
    assert team_response.status_code == 200
    team_data = team_response.json()
    assert len(team_data["artefact_matching_rules"]) == 1
    assert team_data["artefact_matching_rules"][0]["id"] == rule_id

    # Verify the team appears in the rule via rules API
    rule_get_response = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefact-matching-rules/{rule_id}"),
        Permission.view_team,
    )
    assert rule_get_response.status_code == 200
    rule_data = rule_get_response.json()
    assert len(rule_data["teams"]) == 1
    assert rule_data["teams"][0]["id"] == team.id
    assert rule_data["teams"][0]["name"] == "test-team"


def test_create_rule_with_multiple_teams_association(
    test_client: TestClient, generator: DataGenerator
):
    """Test creating a rule with multiple teams"""
    team1 = generator.gen_team(name="team1")
    team2 = generator.gen_team(name="team2")
    
    # Create rule with both teams
    rule_response = make_authenticated_request(
        lambda: test_client.post(
            "/v1/artefact-matching-rules",
            json={
                "family": "snap",
                "track": "22",
                "stage": "stable",
                "team_ids": [team1.id, team2.id],
            },
        ),
        Permission.change_team,
    )
    assert rule_response.status_code == 201
    rule_id = rule_response.json()["id"]

    # Verify both teams show in the rule
    rule_get = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefact-matching-rules/{rule_id}"),
        Permission.view_team,
    )
    assert rule_get.status_code == 200
    rule_data = rule_get.json()
    assert len(rule_data["teams"]) == 2
    team_names = {t["name"] for t in rule_data["teams"]}
    assert team_names == {"team1", "team2"}
    
    # Verify the rule appears in both teams
    for team in [team1, team2]:
        team_get = make_authenticated_request(
            lambda: test_client.get(f"/v1/teams/{team.id}"),
            Permission.view_team,
        )
        assert team_get.status_code == 200
        team_data = team_get.json()
        rule_ids = [r["id"] for r in team_data["artefact_matching_rules"]]
        assert rule_id in rule_ids
