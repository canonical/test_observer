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

from fastapi import APIRouter, Depends
from sqlalchemy import distinct, select
from sqlalchemy.orm import Session
from . import reported_issues
from .models import EnvironmentsResponse

from test_observer.data_access.models import Environment, TestExecution, TestResult
from test_observer.data_access.setup import get_db

router = APIRouter(tags=["environments"])
router.include_router(reported_issues.router)


@router.get("", response_model=EnvironmentsResponse)
def get_environments(
    db: Session = Depends(get_db),
) -> EnvironmentsResponse:
    """
    Returns list of distinct environments.
    """

    query = (
        select(distinct(Environment.name))
        .order_by(Environment.name)
    )

    environments = db.execute(query).scalars().all()
    return EnvironmentsResponse(environments=list(environments))
