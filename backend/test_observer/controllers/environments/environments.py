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

from typing import Annotated
from fastapi import APIRouter, Depends, Query, Security
from sqlalchemy import distinct, select
from sqlalchemy.orm import Session

from . import reported_issues
from .models import EnvironmentsResponse

from test_observer.common.permissions import Permission, permission_checker
from test_observer.data_access.models import (
    Environment,
)
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

    # Apply search filter if provided
    if q and q.strip():
        search_term = f"%{q.strip()}%"
        query = query.where(Environment.name.ilike(search_term))

    # Apply pagination
    query = query.offset(offset).limit(limit)

    environments = db.execute(query).scalars().all()
    return EnvironmentsResponse(environments=list(environments))
