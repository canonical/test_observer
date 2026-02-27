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

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from test_observer.common.permissions import Permission, permission_checker
from test_observer.controllers.teams.models import (
    TeamCreate,
    TeamPatch,
    TeamResponse,
    UserMinimalResponse,
)
from test_observer.controllers.common.artefact_matching_rule_models import (
    ArtefactMatchingRuleInResponse,
)
from test_observer.data_access.models import Team, User, ArtefactMatchingRule
from test_observer.data_access.setup import get_db

router: APIRouter = APIRouter(tags=["teams"])


def _get_team_or_raise_404(db: Session, team_id: int) -> Team:
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail=f"Team {team_id} doesn't exist")
    return team


def _get_user_or_raise_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User {user_id} doesn't exist")
    return user


def _sync_artefact_matching_rules(db: Session, team: Team, rules_data: list):
    """
    Sync artefact matching rules by creating/removing ArtefactMatchingRules.
    Replaces all existing rules for the team with the provided ones.
    """
    # Clear existing rules for this team (make a copy first)
    removed_rules = list(team.artefact_matching_rules)
    team.artefact_matching_rules.clear()
    
    # Deduplicate rules in the request
    seen_rules = set()
    unique_rules_data = []
    for rule_data in rules_data:
        rule_key = (rule_data.family, rule_data.stage, rule_data.track, rule_data.branch)
        if rule_key not in seen_rules:
            seen_rules.add(rule_key)
            unique_rules_data.append(rule_data)
    
    # Add new rules
    for rule_data in unique_rules_data:
        # Check if an identical rule already exists
        existing_rule = db.execute(
            select(ArtefactMatchingRule).where(
                ArtefactMatchingRule.family == rule_data.family,
                ArtefactMatchingRule.stage == rule_data.stage,
                ArtefactMatchingRule.track == rule_data.track,
                ArtefactMatchingRule.branch == rule_data.branch,
            )
        ).scalar_one_or_none()
        
        if existing_rule:
            # Use existing rule
            team.artefact_matching_rules.append(existing_rule)
        else:
            # Create new rule
            new_rule = ArtefactMatchingRule(
                family=rule_data.family,
                stage=rule_data.stage,
                track=rule_data.track,
                branch=rule_data.branch,
                teams=[team]
            )
            db.add(new_rule)

    # Flush to synchronize relationships before checking for orphans
    db.flush()

    # Cleanup orphaned rules
    for rule in removed_rules:
        if not rule.teams:
            db.delete(rule)


def _team_to_response(team: Team) -> TeamResponse:
    """Convert Team model to TeamResponse"""
    return TeamResponse(
        id=team.id,
        name=team.name,
        permissions=team.permissions,
        members=[
            UserMinimalResponse(
                id=user.id,
                launchpad_handle=user.launchpad_handle,
                email=user.email,
                name=user.name,
                is_admin=user.is_admin,
            )
            for user in team.members
        ],
        reviewer_families=team.reviewer_families,
        artefact_matching_rules=[
            ArtefactMatchingRuleInResponse(
                id=rule.id,
                family=rule.family,
                stage=rule.stage,
                track=rule.track,
                branch=rule.branch,
            )
            for rule in team.artefact_matching_rules
        ],
    )


@router.post(
    "",
    response_model=TeamResponse,
    status_code=201,
    dependencies=[Security(permission_checker, scopes=[Permission.change_team])],
)
def create_team(
    request: TeamCreate,
    db: Session = Depends(get_db),
):
    """Create a new team"""
    team = Team(
        name=request.name,
        permissions=[p.value for p in request.permissions],
        reviewer_families=request.reviewer_families,
    )
    db.add(team)
    try:
        db.flush()  # Flush to get the team ID
        if request.artefact_matching_rules:
            _sync_artefact_matching_rules(db, team, request.artefact_matching_rules)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Team with name '{request.name}' already exists") from None
    db.refresh(team)
    return _team_to_response(team)


@router.get(
    "",
    response_model=list[TeamResponse],
    dependencies=[Security(permission_checker, scopes=[Permission.view_team])],
)
def get_teams(
    db: Session = Depends(get_db),
):
    teams = db.scalars(select(Team)).all()
    return [_team_to_response(team) for team in teams]


@router.get(
    "/{team_id}",
    response_model=TeamResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_team])],
)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
):
    team = _get_team_or_raise_404(db, team_id)
    return _team_to_response(team)


@router.patch(
    "/{team_id}",
    response_model=TeamResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.change_team])],
)
def update_team(
    team_id: int,
    request: TeamPatch,
    db: Session = Depends(get_db),
):
    team = _get_team_or_raise_404(db, team_id)

    if request.permissions:
        team.permissions = [p.value for p in request.permissions]

    if request.reviewer_families is not None:
        team.reviewer_families = request.reviewer_families

    if request.artefact_matching_rules is not None:
        _sync_artefact_matching_rules(db, team, request.artefact_matching_rules)

    db.commit()
    db.refresh(team)

    return _team_to_response(team)


@router.post(
    "/{team_id}/members/{user_id}",
    response_model=TeamResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.change_team])],
)
def add_team_member(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    """Add a user to a team"""
    team = _get_team_or_raise_404(db, team_id)
    user = _get_user_or_raise_404(db, user_id)

    # Check if user is already a member
    if user not in team.members:
        team.members.append(user)
        db.commit()
        db.refresh(team)

    return _team_to_response(team)


@router.delete(
    "/{team_id}/members/{user_id}",
    response_model=TeamResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.change_team])],
)
def remove_team_member(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    """Remove a user from a team"""
    team = _get_team_or_raise_404(db, team_id)
    user = _get_user_or_raise_404(db, user_id)

    # Check if user is a member
    if user in team.members:
        team.members.remove(user)
        db.commit()
        db.refresh(team)

    return _team_to_response(team)
