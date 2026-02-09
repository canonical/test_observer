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
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from test_observer.data_access.models import TestExecution
from test_observer.data_access.models_enums import (
    FamilyName,
    SnapStage,
    DebStage,
    CharmStage,
)
from test_observer.common.permissions import Permission
from tests.data_generator import DataGenerator
from tests.conftest import make_authenticated_request


@pytest.fixture
def start_test(test_client: TestClient):
    def _start_test(data: dict) -> dict:
        json_data = jsonable_encoder(data)
        response = make_authenticated_request(
            lambda: test_client.put("/v1/test-executions/start-test", json=json_data),
            Permission.change_test,
        )
        assert response.status_code == 200, f"Error {response.status_code}: {response.text}"
        return response.json()

    return _start_test


class TestReviewerAssignmentWithMatchingRules:
    """Tests for reviewer assignment based on ArtefactMatchingRule"""

    @pytest.mark.parametrize(
        "setup_data, artefact_params, expected_user_names",
        [
            pytest.param(
                {
                    "teams": [{"name": "snap-team", "users": ["SnapUser"]}],
                    "rules": [{"family": FamilyName.snap, "team": "snap-team"}],
                },
                {
                    "family": "snap", 
                    "name": "core22", 
                    "execution_stage": SnapStage.beta,
                    "track": "22",
                    "store": "ubuntu",
                    "revision": 1,
                },
                ["SnapUser"],
                id="match-family-only",
            ),
            pytest.param(
                {
                    "teams": [{"name": "beta-team", "users": ["BetaUser"]}],
                    "rules": [{"family": FamilyName.snap, "stage": SnapStage.beta, "team": "beta-team"}],
                },
                {
                    "family": "snap", 
                    "name": "core22", 
                    "execution_stage": SnapStage.beta,
                    "track": "22",
                    "store": "ubuntu",
                    "revision": 1,
                },
                ["BetaUser"],
                id="match-family-and-stage",
            ),
            pytest.param(
                {
                    "teams": [{"name": "deb-team", "users": ["DebUser"]}],
                    "rules": [{"family": FamilyName.deb, "stage": DebStage.proposed, "team": "deb-team"}],
                },
                {
                    "family": "deb", 
                    "name": "linux", 
                    "execution_stage": DebStage.proposed, 
                    "series": "jammy", 
                    "repo": "main"
                },
                ["DebUser"],
                id="match-deb-artefact",
            ),
            pytest.param(
                {
                    "teams": [{"name": "charm-team", "users": ["CharmUser"]}],
                    "rules": [{"family": FamilyName.charm, "stage": CharmStage.beta, "team": "charm-team"}],
                },
                {
                    "family": "charm", 
                    "name": "postgresql", 
                    "execution_stage": CharmStage.beta,
                    "track": "3.0",
                    "revision": 1,
                },
                ["CharmUser"],
                id="match-charm-artefact",
            ),
            pytest.param(
                {
                    "teams": [{"name": "charm-team", "users": ["CharmUser"]},  {"name": "beta-team", "users": ["BetaUser"]}],
                    "rules": [{"family": FamilyName.charm, "team": "charm-team"}, {"family": FamilyName.charm, "stage": CharmStage.beta, "team": "beta-team"}],
                },
                {
                    "family": "charm", 
                    "name": "postgresql", 
                    "execution_stage": CharmStage.beta,
                    "track": "3.0",
                    "revision": 1,
                },
                ["BetaUser"],
                id="match-twice-with-different-specificity",
            ),
        ],
    )
    def test_reviewer_assignment_scenarios(
        self,
        start_test,
        db_session: Session,
        generator: DataGenerator,
        setup_data,
        artefact_params,
        expected_user_names,
    ):
        # GIVEN users and teams
        user_map = {}
        team_map = {}
        
        for team_conf in setup_data["teams"]:
            team = generator.gen_team(name=team_conf["name"])
            team_map[team_conf["name"]] = team
            for username in team_conf["users"]:
                user = generator.gen_user(
                    name=username, 
                    email=f"{username.lower()}@test.com", 
                    teams=[team]
                )
                user_map[username] = user

        # GIVEN matching rules
        for rule_conf in setup_data["rules"]:
            config = rule_conf.copy()
            team_name = config.pop("team")
            team_obj = team_map[team_name]
            generator.gen_artefact_matching_rule(teams=[team_obj], **config)

        # WHEN starting a test execution
        request_data = {
            "version": "v1",
            "arch": "amd64",
            "environment": "env",
            "ci_link": "http://test.com",
            "test_plan": "test",
            "needs_assignment": True,
        }
        request_data.update(artefact_params)

        result = start_test(request_data)

        # THEN the test execution's artefact is assigned to the expected user
        test_execution = db_session.get(TestExecution, result["id"])
        assignee = test_execution.artefact_build.artefact.assignee
        
        if not expected_user_names:
            assert assignee is None
        else:
            assert assignee is not None
            assert assignee.name in expected_user_names
