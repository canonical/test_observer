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

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from test_observer.common.permissions import Permission, permission_checker
from test_observer.controllers.artefact_matching_rules.models import (
    ArtefactMatchingRuleRequest,
    ArtefactMatchingRulePatch,
    ArtefactMatchingRuleResponse,
    TeamMinimal,
)
from test_observer.data_access.models import ArtefactMatchingRule, Team
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.setup import get_db


router: APIRouter = APIRouter(tags=["artefact-matching-rules"])


def _get_rule_or_raise_404(db: Session, rule_id: int) -> ArtefactMatchingRule:
    rule = db.get(ArtefactMatchingRule, rule_id)
    if rule is None:
        raise HTTPException(
            status_code=404, detail=f"Artefact matching rule {rule_id} doesn't exist"
        )
    return rule


def _rule_to_response(rule: ArtefactMatchingRule) -> ArtefactMatchingRuleResponse:
    """Convert ArtefactMatchingRule model to response"""
    return ArtefactMatchingRuleResponse(
        id=rule.id,
        family=rule.family,
        stage=rule.stage,
        track=rule.track,
        branch=rule.branch,
        teams=[TeamMinimal(id=team.id, name=team.name) for team in rule.teams],
    )


@router.post(
    "",
    response_model=ArtefactMatchingRuleResponse,
    status_code=201,
    dependencies=[Security(permission_checker, scopes=[Permission.change_team])],
)
def create_artefact_matching_rule(
    request: ArtefactMatchingRuleRequest,
    db: Session = Depends(get_db),
):
    """Create a new artefact matching rule with at least one team"""
    # Validate that team_ids is not empty
    if not request.team_ids:
        raise HTTPException(
            status_code=400,
            detail="At least one team is required to create a matching rule",
        )

    # Validate that all teams exist
    teams = []
    for team_id in request.team_ids:
        team = db.get(Team, team_id)
        if not team:
            raise HTTPException(
                status_code=404,
                detail=f"Team {team_id} doesn't exist",
            )
        teams.append(team)

    # Check if rule already exists
    existing_rule = db.execute(
        select(ArtefactMatchingRule).where(
            ArtefactMatchingRule.family == request.family,
            ArtefactMatchingRule.stage == request.stage,
            ArtefactMatchingRule.track == request.track,
            ArtefactMatchingRule.branch == request.branch,
        )
    ).scalar_one_or_none()

    if existing_rule:
        raise HTTPException(
            status_code=409,
            detail="Artefact matching rule with these values already exists",
        )

    rule = ArtefactMatchingRule(
        family=request.family,
        stage=request.stage,
        track=request.track,
        branch=request.branch,
        teams=teams,
    )
    db.add(rule)
    try:
        db.commit()
        db.refresh(rule)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Artefact matching rule with these values already exists",
        ) from None

    return _rule_to_response(rule)


@router.get(
    "",
    response_model=list[ArtefactMatchingRuleResponse],
    dependencies=[Security(permission_checker, scopes=[Permission.view_team])],
)
def get_artefact_matching_rules(
    db: Session = Depends(get_db),
    family: FamilyName | None = None,
):
    """Get all artefact matching rules, optionally filtered by family"""
    query = select(ArtefactMatchingRule)

    if family:
        query = query.where(ArtefactMatchingRule.family == family)

    rules = db.scalars(query).all()
    return [_rule_to_response(rule) for rule in rules]


@router.get(
    "/{rule_id}",
    response_model=ArtefactMatchingRuleResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_team])],
)
def get_artefact_matching_rule(
    rule_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific artefact matching rule by ID"""
    rule = _get_rule_or_raise_404(db, rule_id)
    return _rule_to_response(rule)


@router.patch(
    "/{rule_id}",
    response_model=ArtefactMatchingRuleResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.change_team])],
)
def update_artefact_matching_rule(
    rule_id: int,
    request: ArtefactMatchingRulePatch,
    db: Session = Depends(get_db),
):
    """Update an artefact matching rule"""
    rule = _get_rule_or_raise_404(db, rule_id)

    # Check if at least one field is being updated
    if request.family is None:
        raise HTTPException(
            status_code=400,
            detail="Family field is required and cannot be set to None",
        )

    # Validate team_ids if provided
    if request.team_ids is not None:
        if not request.team_ids:
            raise HTTPException(
                status_code=400,
                detail="At least one team is required. Use DELETE to remove the rule.",
            )

        # Validate that all teams exist
        teams = []
        for team_id in request.team_ids:
            team = db.get(Team, team_id)
            if not team:
                raise HTTPException(
                    status_code=404,
                    detail=f"Team {team_id} doesn't exist",
                )
            teams.append(team)

    # Check if updated rule would conflict with existing rule
    existing_rule = db.execute(
        select(ArtefactMatchingRule).where(
            ArtefactMatchingRule.family == request.family,
            ArtefactMatchingRule.stage == request.stage,
            ArtefactMatchingRule.track == request.track,
            ArtefactMatchingRule.branch == request.branch,
            ArtefactMatchingRule.id != rule_id,
        )
    ).scalar_one_or_none()

    if existing_rule:
        raise HTTPException(
            status_code=409,
            detail="Another artefact matching rule with these values already exists",
        )

    # Update fields
    rule.family = request.family
    rule.stage = request.stage
    rule.track = request.track
    rule.branch = request.branch

    # Update teams if provided
    if request.team_ids is not None:
        rule.teams = teams

    try:
        db.commit()
        db.refresh(rule)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Another artefact matching rule with these values already exists",
        ) from None

    return _rule_to_response(rule)


@router.delete(
    "/{rule_id}",
    status_code=204,
    dependencies=[Security(permission_checker, scopes=[Permission.change_team])],
)
def delete_artefact_matching_rule(
    rule_id: int,
    db: Session = Depends(get_db),
):
    """Delete an artefact matching rule"""
    rule = _get_rule_or_raise_404(db, rule_id)

    db.delete(rule)
    db.commit()
