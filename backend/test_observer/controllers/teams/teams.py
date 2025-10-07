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
from sqlalchemy.orm import Session

from test_observer.common.permissions import Permission, permission_checker
from test_observer.controllers.teams.models import TeamPatch, TeamResponse
from test_observer.data_access.models import Team
from test_observer.data_access.setup import get_db


router: APIRouter = APIRouter(tags=["teams"])


@router.get(
    "",
    response_model=list[TeamResponse],
    dependencies=[Security(permission_checker, scopes=[Permission.view_team])],
)
def get_teams(
    db: Session = Depends(get_db),
):
    return db.scalars(select(Team))


@router.get(
    "/{team_id}",
    response_model=TeamResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_team])],
)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
):
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(404, f"Team {team_id} doesn't exist")
    return team


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
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(404, f"Team {team_id} doesn't exist")

    if request.permissions:
        team.permissions = [p.value for p in request.permissions]
        db.commit()

    return team
