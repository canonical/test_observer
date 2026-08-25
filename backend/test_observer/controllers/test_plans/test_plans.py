# Copyright 2026 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Security
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from test_observer.common.enums import Permission
from test_observer.common.permissions import permission_checker
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    TestExecution,
    TestPlan,
)
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.setup import get_db

from .models import TestPlansResponse

router = APIRouter(tags=["test-plans"])


@router.get(
    "",
    response_model=TestPlansResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_test])],
)
def get_test_plans(
    q: Annotated[
        str | None,
        Query(description="Search term for test plan names"),
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
) -> TestPlansResponse:
    """
    Returns list of distinct test plan names that have been used in test executions.

    Supports pagination and search filtering.
    """
    query = (
        select(distinct(TestPlan.name))
        .join(TestExecution, TestExecution.test_plan_id == TestPlan.id)
        .order_by(TestPlan.name)
    )

    # Filter by families if provided
    if families and len(families) > 0:
        query = query.join(ArtefactBuild, ArtefactBuild.id == TestExecution.artefact_build_id).join(
            Artefact, Artefact.id == ArtefactBuild.artefact_id
        )
        query = query.where(Artefact.family.in_(families))

    # Apply search filter if provided
    if q and q.strip():
        search_term = f"%{q.strip()}%"
        query = query.where(TestPlan.name.ilike(search_term))

    # Count total before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_count = db.execute(count_query).scalar() or 0

    # Apply pagination
    query = query.offset(offset).limit(limit)

    test_plans = db.execute(query).scalars().all()
    return TestPlansResponse(
        test_plans=list(test_plans),
        count=total_count,
        limit=limit,
        offset=offset,
    )
