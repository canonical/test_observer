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

from typing import Annotated
from fastapi import APIRouter, Depends, Query, Security
from sqlalchemy import distinct, select
from sqlalchemy.orm import Session

from . import reported_issues
from .models import EnvironmentsResponse

from test_observer.common.permissions import Permission, permission_checker
from test_observer.data_access.models import (
    Environment,
    TestExecution,
    ArtefactBuild,
    Artefact,
)
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.setup import get_db

router = APIRouter(tags=["environments"])
router.include_router(reported_issues.router)


@router.get(
    "",
    response_model=EnvironmentsResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_test])],
)
def get_environments(
    q: Annotated[
        str | None,
        Query(description="Search term for environment names"),
    ] = None,
    families: Annotated[
        list[FamilyName] | None,
        Query(description="Filter by artefact families"),
    ] = None,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=1000,
            description="Maximum number of results (defaults to 50 if not specified)",
        ),
    ] = 50,
    offset: Annotated[
        int,
        Query(ge=0, description="Number of results to skip for pagination"),
    ] = 0,
    db: Session = Depends(get_db),
) -> EnvironmentsResponse:
    """
    Returns list of distinct environments that have been used in test executions.

    Supports pagination and search filtering.
    """
    query = select(distinct(Environment.name)).order_by(Environment.name)

    # Filter by families if provided
    if families and len(families) > 0:
        query = (
            query.join(TestExecution, TestExecution.environment_id == Environment.id)
            .join(ArtefactBuild, ArtefactBuild.id == TestExecution.artefact_build_id)
            .join(Artefact, Artefact.id == ArtefactBuild.artefact_id)
            .where(Artefact.family.in_(families))
        )

    # Apply search filter if provided
    if q and q.strip():
        search_term = f"%{q.strip()}%"
        query = query.where(Environment.name.ilike(search_term))

    # Apply pagination
    query = query.offset(offset).limit(limit)

    environments = db.execute(query).scalars().all()
    return EnvironmentsResponse(environments=list(environments))
