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

from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import and_, desc, select, func
from sqlalchemy.orm import Session, joinedload

from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    TestExecution,
    TestResult,
    TestCase,
    Issue,
    IssueTestResultAttachment,
)
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.setup import get_db

from .models import TestResultSearchResponse

router = APIRouter(tags=["test-results"])


def parse_csv_values(values: str) -> list[str]:
    """Parse comma-separated values and return list of stripped non-empty values."""
    return [value.strip() for value in values.split(",") if value.strip()]


def parse_csv_ids(ids: str) -> list[int]:
    """Parse comma-separated IDs and return list of integers."""
    try:
        return [int(id_str) for id_str in parse_csv_values(ids)]
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid ID format"
            ) from None


@router.get("", response_model=TestResultSearchResponse)
def search_test_results(
    families: str | None = Query(
        None, description="Filter by artefact families (e.g., charm,snap)"
    ),
    environments: str | None = Query(
        None,
        description="Filter by environment names (e.g., Juju:3/stable ubuntu:20.04)",
    ),
    test_cases: str | None = Query(
        None, description="Filter by test case names (e.g., test_deploy)"
    ),
    template_ids: str | None = Query(None, description="Filter by template IDs"),
    issues: str | None = Query(
        None, description="Filter by Jira or GitHub issue IDs (comma-separated)"
    ),
    from_date: datetime | None = Query(
        None, description="Filter results from this timestamp"
    ),
    until_date: datetime | None = Query(
        None, description="Filter results until this timestamp"
    ),
    limit: int = Query(
        50, ge=1, le=1000, description="Maximum number of results to return"
    ),
    offset: int = Query(
        0, ge=0, description="Number of results to skip for pagination"
    ),
    db: Session = Depends(get_db),
) -> TestResultSearchResponse:
    """
    Search test results across artefacts using flexible filters.

    This endpoint uses a single optimized query with window functions to get both
    the total count and paginated results in one database round trip.
    """

    # Build filters
    filters = []

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

        filters.append(Artefact.family.in_(family_enums))

    if environments:
        environment_list = parse_csv_values(environments)
        filters.append(Environment.name.in_(environment_list))

    if test_cases:
        test_case_list = parse_csv_values(test_cases)
        filters.append(TestCase.name.in_(test_case_list))

    if template_ids:
        template_id_list = parse_csv_values(template_ids)
        filters.append(TestCase.template_id.in_(template_id_list))

    if issues:
        issue_ids = parse_csv_ids(issues)
        filters.append(
            TestResult.id.in_(
                select(IssueTestResultAttachment.test_result_id)
                .join(IssueTestResultAttachment.issue)
                .where(Issue.id.in_(issue_ids))
            )
        )

    if from_date:
        filters.append(TestExecution.created_at >= from_date) # type: ignore

    if until_date:
        filters.append(TestExecution.created_at <= until_date) # type: ignore

    # Build the main query with window function for total count in a single query
    query = (
        select(TestResult, func.count().over().label("total_count"))
        .join(TestResult.test_execution)
        .join(TestExecution.environment)
        .join(TestExecution.artefact_build)
        .join(ArtefactBuild.artefact)
        .join(TestResult.test_case)
        .options(
            joinedload(TestResult.test_execution).joinedload(TestExecution.environment),
            joinedload(TestResult.test_execution)
            .joinedload(TestExecution.artefact_build)
            .joinedload(ArtefactBuild.artefact),
            joinedload(TestResult.test_case),
        )
        .order_by(desc(TestExecution.created_at), desc(TestResult.id))
        .offset(offset)
        .limit(limit)
    )

    # Apply all filters
    if filters:
        query = query.where(and_(*filters))

    result = db.execute(query).all()

    if result:
        test_results = [row[0] for row in result]
        total_count = result[0][1]
    else:
        test_results = []
        total_count = 0

    return TestResultSearchResponse(count=total_count, test_results=test_results)

