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

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from test_observer.common.enums import Permission
from test_observer.common.permissions import check_amr_permission
from test_observer.data_access.models_enums import FamilyName, StageName
from tests.data_generator import DataGenerator


class TestCheckAMRPermission:
    """Test AMR-based permission checking"""

    def test_user_in_matching_amr_team_has_permission(self, generator: DataGenerator, db_session: Session):
        """User in a team that matches the artefact's AMR should have the permission"""
        # Create a team and an artefact matching rule granting change_artefact
        team = generator.gen_team(name="snap-team")
        generator.gen_artefact_matching_rule(
            family=FamilyName.snap,
            stage="stable",
            teams=[team],
            grant_permissions=[Permission.change_artefact],
        )

        # Create an artefact that matches the rule
        artefact = generator.gen_artefact(
            name="test-snap",
            family=FamilyName.snap,
            stage=StageName.stable,
        )

        # Create a user in the team
        user = generator.gen_user(name="alice")
        user.teams = [team]
        generator._add_object(user)

        # Should not raise when user is in matching team
        check_amr_permission(
            db_session,
            user,
            artefact,
            Permission.change_artefact,
        )

    def test_user_not_in_matching_amr_team_denied(self, generator: DataGenerator, db_session: Session):
        """User not in the team that matches the artefact's AMR should be denied"""
        # Create two teams
        team1 = generator.gen_team(name="team-a")
        team2 = generator.gen_team(name="team-b")

        # Create an AMR for team1
        generator.gen_artefact_matching_rule(
            family=FamilyName.snap,
            stage="stable",
            teams=[team1],
            grant_permissions=[Permission.change_artefact],
        )

        # Create an artefact matching the rule
        artefact = generator.gen_artefact(
            name="test-snap",
            family=FamilyName.snap,
            stage=StageName.stable,
        )

        # Create a user in team2 (not team1)
        user = generator.gen_user(name="bob")
        user.teams = [team2]
        generator._add_object(user)

        # Should raise 403 when user is not in matching team
        with pytest.raises(HTTPException) as exc_info:
            check_amr_permission(
                db_session,
                user,
                artefact,
                Permission.change_artefact,
            )
        assert exc_info.value.status_code == 403

    def test_user_with_no_teams_denied(self, generator: DataGenerator, db_session: Session):
        """User with no teams should be denied"""
        # Create a team and AMR
        team = generator.gen_team(name="snap-team")
        generator.gen_artefact_matching_rule(
            family=FamilyName.snap,
            stage="stable",
            teams=[team],
            grant_permissions=[Permission.change_artefact],
        )

        # Create an artefact
        artefact = generator.gen_artefact(
            name="test-snap",
            family=FamilyName.snap,
            stage=StageName.stable,
        )

        # Create a user with no teams
        user = generator.gen_user(name="charlie")
        user.teams = []
        generator._add_object(user)

        # Should raise 403
        with pytest.raises(HTTPException) as exc_info:
            check_amr_permission(
                db_session,
                user,
                artefact,
                Permission.change_artefact,
            )
        assert exc_info.value.status_code == 403

    def test_no_matching_amr_denied(self, generator: DataGenerator, db_session: Session):
        """If no AMR matches the artefact, access should be denied"""
        # Create a team and AMR for snap on stable
        team = generator.gen_team(name="snap-team")
        generator.gen_artefact_matching_rule(
            family=FamilyName.snap,
            stage="stable",
            teams=[team],
            grant_permissions=[Permission.change_artefact],
        )

        # Create an artefact that does NOT match (different stage)
        artefact = generator.gen_artefact(
            name="test-snap",
            family=FamilyName.snap,
            stage=StageName.beta,
        )

        # Create user in team
        user = generator.gen_user(name="dave")
        user.teams = [team]
        generator._add_object(user)

        # Should raise 403 because no AMR matches this artefact
        with pytest.raises(HTTPException) as exc_info:
            check_amr_permission(
                db_session,
                user,
                artefact,
                Permission.change_artefact,
            )
        assert exc_info.value.status_code == 403

    def test_required_permission_not_granted_by_amr(self, generator: DataGenerator, db_session: Session):
        """If AMR doesn't grant the required permission, access should be denied"""
        # Create a team and AMR that grants view_artefact but not change_artefact
        team = generator.gen_team(name="snap-team")
        generator.gen_artefact_matching_rule(
            family=FamilyName.snap,
            stage="stable",
            teams=[team],
            grant_permissions=[Permission.view_artefact],
        )

        # Create matching artefact
        artefact = generator.gen_artefact(
            name="test-snap",
            family=FamilyName.snap,
            stage=StageName.stable,
        )

        # Create user in team
        user = generator.gen_user(name="eve")
        user.teams = [team]
        generator._add_object(user)

        # Should raise 403 because change_artefact is not granted
        with pytest.raises(HTTPException) as exc_info:
            check_amr_permission(
                db_session,
                user,
                artefact,
                Permission.change_artefact,
            )
        assert exc_info.value.status_code == 403

    def test_user_in_one_of_multiple_equally_specific_amrs(self, generator: DataGenerator, db_session: Session):
        """User in one team of multiple equally-specific matching AMRs should have permission"""
        # Create two teams
        team1 = generator.gen_team(name="team-a")
        team2 = generator.gen_team(name="team-b")

        # Create two AMRs with equal specificity (both family+stage) but different names
        generator.gen_artefact_matching_rule(
            name="rule-1",
            family=FamilyName.snap,
            stage="stable",
            teams=[team1],
            grant_permissions=[Permission.change_artefact],
        )

        generator.gen_artefact_matching_rule(
            name="rule-2",
            family=FamilyName.snap,
            stage="stable",
            teams=[team2],
            grant_permissions=[Permission.change_artefact],
        )

        # Create artefact matching both AMRs
        artefact = generator.gen_artefact(
            name="test-snap",
            family=FamilyName.snap,
            stage=StageName.stable,
        )

        # Create user in team1 (one of the two equally-specific AMRs)
        user = generator.gen_user(name="grace", email="grace@example.com")
        user.teams = [team1]
        generator._add_object(user)

        # Should have permission through team1's AMR
        check_amr_permission(
            db_session,
            user,
            artefact,
            Permission.change_artefact,
        )

        # Also test user in team2
        user2 = generator.gen_user(name="henry", email="henry@example.com")
        user2.teams = [team2]
        generator._add_object(user2)

        # Should also have permission through team2's AMR
        check_amr_permission(
            db_session,
            user2,
            artefact,
            Permission.change_artefact,
        )

    def test_specificity_score_calculation(self, generator: DataGenerator, db_session: Session):
        """Best-matching AMR should be selected by specificity score"""
        # Create two teams
        team_general = generator.gen_team(name="general-team")
        team_specific = generator.gen_team(name="specific-team")

        # Create a general AMR (matches all snaps)
        generator.gen_artefact_matching_rule(
            family=FamilyName.snap,
            teams=[team_general],
            grant_permissions=[Permission.view_artefact],
        )

        # Create a specific AMR (matches snaps on stable track)
        generator.gen_artefact_matching_rule(
            family=FamilyName.snap,
            track="stable",
            teams=[team_specific],
            grant_permissions=[Permission.change_artefact],
        )

        # Create artefact that matches both (but rule_specific is more specific)
        artefact = generator.gen_artefact(
            name="test-snap",
            family=FamilyName.snap,
            track="stable",
        )

        # Create user only in the specific team
        user = generator.gen_user(name="grace")
        user.teams = [team_specific]
        generator._add_object(user)

        # Should grant change_artefact from the specific AMR, not view_artefact from general
        check_amr_permission(
            db_session,
            user,
            artefact,
            Permission.change_artefact,
        )

    def test_none_user_raises_error(self, generator: DataGenerator, db_session: Session):
        """Passing None as user should raise HTTPException"""
        # Create artefact
        artefact = generator.gen_artefact(
            name="test-snap",
            family=FamilyName.snap,
            stage=StageName.stable,
        )

        # Should raise 403 when user is None
        with pytest.raises(HTTPException) as exc_info:
            check_amr_permission(
                db_session,
                None,
                artefact,
                Permission.change_artefact,
            )
        assert exc_info.value.status_code == 403
