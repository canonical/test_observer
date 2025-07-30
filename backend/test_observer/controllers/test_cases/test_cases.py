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
from sqlalchemy import distinct, select
from sqlalchemy.orm import Session

from . import reported_issues
from .models import TestCasesResponse

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
    return [value.strip() for value in values.split(",") if value.strip()]


@router.get("", response_model=TestCasesResponse)
def get_test_cases(
    families: str | None = Query(None, description="Filter test cases by families"),
    environments: str | None = Query(
        None, description="Filter test cases by environments"
    ),
    db: Session = Depends(get_db),
) -> TestCasesResponse:
    """
    Returns test cases with their template IDs, optionally filtered by other criteria.
    """

    query = (
        select(distinct(TestCase.name), TestCase.template_id)
        .join(TestResult)
        .join(TestResult.test_execution)
        .join(TestExecution.artefact_build)
        .join(ArtefactBuild.artefact)
        .join(TestExecution.environment)
    )

    # Apply cascading filters
    if families:
        family_list = parse_csv_values(families)
        family_enums = []
        for family in family_list:
            try:
                family_enums.append(FamilyName(family.lower()))
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid family: {family}"
                ) from None

        query = query.where(Artefact.family.in_(family_enums))

    if environments:
        environment_list = parse_csv_values(environments)
        query = query.where(Environment.name.in_(environment_list))

    query = query.order_by(TestCase.name)

    test_cases_data = db.execute(query).all()

    # Group by test case name and collect template IDs
    test_cases_dict: dict[str, list[dict[str, str]]] = {}
    for name, template_id in test_cases_data:
        if name not in test_cases_dict:
            test_cases_dict[name] = []
        if template_id and {"template": template_id} not in test_cases_dict[name]:
            test_cases_dict[name].append({"template": template_id})

    return TestCasesResponse(test_cases=test_cases_dict)
