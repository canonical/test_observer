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
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from . import reported_issues
from .models import TestCasesResponse, TestCaseInfo

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

router = APIRouter(tags=["test-cases"])
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


@router.get("", response_model=TestCasesResponse)
def get_test_cases(
    families: str | None = Query(None, description="Filter test cases by families"),
    environments: str | None = Query(
        None, description="Filter test cases by environments"
    ),
    db: Session = Depends(get_db),
) -> TestCasesResponse:
    """
    Returns test cases as a flat list with their template IDs.

    Template ID represents the generic test (e.g., "disk/stats_name")
    Test case name is the specific instance (e.g., "disk/stats_nvme0n1")
    Multiple test cases can share the same template ID but have different names.
    """

    filters = []

    if families:
        family_enums = parse_family_enums(families)
        filters.append(Artefact.family.in_(family_enums))

    if environments:
        environment_list = parse_csv_values(environments)
        if len(environment_list) == 1:
            filters.append(Environment.name.ilike(f"%{environment_list[0]}%"))
        else:
            filters.append(Environment.name.in_(environment_list))

    # Single optimized query with all joins and filters
    base_query = (
        select(
            TestCase.name,
            TestCase.template_id,
        )
        .distinct()
        .join(TestResult)
        .join(TestResult.test_execution)
        .join(TestExecution.artefact_build)
        .join(ArtefactBuild.artefact)
        .join(TestExecution.environment)
    )

    query = base_query.where(and_(*filters)) if filters else base_query
    query = query.order_by(TestCase.name, TestCase.template_id)

    test_cases_data = db.execute(query).all()

    test_cases_list = [
        TestCaseInfo(test_case=name, template_id=template_id or "")
        for name, template_id in test_cases_data
    ]

    return TestCasesResponse(test_cases=test_cases_list)
