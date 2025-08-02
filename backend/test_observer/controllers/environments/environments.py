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

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import distinct, select, and_
from sqlalchemy.orm import Session
from . import reported_issues
from .models import EnvironmentsResponse

from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    TestExecution,
    TestResult,
    TestCase,
)
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.setup import get_db

router = APIRouter(tags=["environments"])
router.include_router(reported_issues.router)


def parse_csv_values(values: str) -> list[str]:
    """Parse comma-separated values and return list of strings."""
    return [value.strip() for value in values.split(",") if value.strip()]


def parse_family_enums(families: str) -> list[FamilyName]:
    """Parse and validate family enums, raising HTTPException for invalid families."""
    family_list = parse_csv_values(families)
    try:
        return [FamilyName(family.lower()) for family in family_list]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid family: {e}") from None


@router.get("", response_model=EnvironmentsResponse)
def get_environments(
    families: str | None = Query(None, description="Filter envs by families"),
    test_cases: str | None = Query(None, description="Filter envs by test cases"),
    db: Session = Depends(get_db),
) -> EnvironmentsResponse:
    """
    Returns list of distinct environments with cascading filters.

    Uses optimized database filtering instead of Python post-processing.
    Only includes environments that have actually been used in test executions.
    """

    filters = []

    if families:
        family_enums = parse_family_enums(families)
        filters.append(Artefact.family.in_(family_enums))

    if test_cases:
        test_case_list = parse_csv_values(test_cases)
        if len(test_case_list) == 1:
            filters.append(TestCase.name.ilike(f"%{test_case_list[0]}%"))
        else:
            filters.append(TestCase.name.in_(test_case_list))

    # Single optimized query with all necessary joins
    if filters:
        query = (
            select(distinct(Environment.name))
            .join(TestExecution)
            .join(TestResult)
            .join(TestCase)
            .join(TestExecution.artefact_build)
            .join(ArtefactBuild.artefact)
            .where(and_(*filters))
            .order_by(Environment.name)
        )
    else:
        query = select(distinct(Environment.name)).order_by(Environment.name)

    environments = db.execute(query).scalars().all()
    return EnvironmentsResponse(environments=list(environments))
