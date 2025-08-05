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
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session, selectinload

from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    Issue,
    IssueTestResultAttachment,
    TestCase,
    TestExecution,
    TestResult,
)
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.setup import get_db

from .models import TestResultSearchResponseWithContext, TestResultResponseWithContext
from test_observer.controllers.test_executions.models import (
    TestResultResponse,
    TestExecutionResponse,
)
from test_observer.controllers.artefacts.models import (
    ArtefactResponse,
    ArtefactBuildMinimalResponse,
)

router = APIRouter(tags=["test-results"])


def parse_csv_values(values: str) -> list[str]:
    """Parse comma-separated values and return list of strings."""
    return [value.strip() for value in values.split(",") if value.strip()]


def parse_csv_ids(ids: str) -> list[int]:
    """Parse comma-separated IDs and return list of integers."""
    try:
        return [int(id_str) for id_str in parse_csv_values(ids)]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format") from None


def parse_family_enums(families: str) -> list[FamilyName]:
    """Parse and validate family enums"""
    family_list = parse_csv_values(families)
    try:
        return [FamilyName(family.lower()) for family in family_list]
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Invalid family: {e}") from None


@router.get("", response_model=TestResultSearchResponseWithContext)
def search_test_results(
    families: Annotated[
        str | None, Query(description="Filter by artefact families (e.g., charm,snap)")
    ] = None,
    environments: Annotated[
        str | None, Query(description="Filter by environment names (comma-separated)")
    ] = None,
    test_cases: Annotated[
        str | None, Query(description="Filter by test case names (comma-separated)")
    ] = None,
    template_ids: Annotated[
        str | None, Query(description="Filter by template IDs (comma-separated)")
    ] = None,
    issues: Annotated[
        str | None,
        Query(description="Filter by Jira or GitHub issue IDs (comma-separated)"),
    ] = None,
    from_date: Annotated[
        datetime | None, Query(description="Filter results from this timestamp")
    ] = None,
    until_date: Annotated[
        datetime | None, Query(description="Filter results until this timestamp")
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=1000, description="Maximum number of results to return")
    ] = 50,
    offset: Annotated[
        int, Query(ge=0, description="Number of results to skip for pagination")
    ] = 0,
    db: Session = Depends(get_db),
) -> TestResultSearchResponseWithContext:
    """
    Search test results across artefacts using flexible filters.

    This endpoint uses a single optimized query with window functions to get both
    the total count and paginated results in one database round trip.
    """

    # Build filters using CSV parsing helper functions
    filters = []

    if families:
        family_list = parse_family_enums(families)
        filters.append(Artefact.family.in_(family_list))

    if environments:
        env_list = parse_csv_values(environments)
        filters.append(Environment.name.in_(env_list))

    if test_cases:
        case_list = parse_csv_values(test_cases)
        filters.append(TestCase.name.in_(case_list))

    if template_ids:
        template_list = parse_csv_values(template_ids)
        filters.append(TestCase.template_id.in_(template_list))

    if issues:
        issue_list = parse_csv_ids(issues)
        filters.append(
            TestResult.id.in_(
                select(IssueTestResultAttachment.test_result_id)
                .join(IssueTestResultAttachment.issue)
                .where(Issue.id.in_(issue_list))
            )
        )

    if from_date:
        filters.append(TestExecution.created_at >= from_date)  # type: ignore

    if until_date:
        filters.append(TestExecution.created_at <= until_date)  # type: ignore

    # Build the main query with window function for total count and proper eager loading
    query = (
        select(TestResult, func.count().over().label("total_count"))
        .join(TestResult.test_execution)
        .join(TestExecution.environment)
        .join(TestExecution.artefact_build)
        .join(ArtefactBuild.artefact)
        .join(TestResult.test_case)
        .options(
            # Load all the related data that the response model needs
            selectinload(TestResult.test_case),
            selectinload(TestResult.test_execution).selectinload(
                TestExecution.environment
            ),
            selectinload(TestResult.test_execution)
            .selectinload(TestExecution.artefact_build)
            .selectinload(ArtefactBuild.artefact),
            selectinload(TestResult.issue_attachments),
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

        enhanced_results = []
        for test_result in test_results:
            test_result_response = TestResultResponse.model_validate(test_result)
            test_execution_response = TestExecutionResponse.model_validate(
                test_result.test_execution
            )
            artefact_response = ArtefactResponse.model_validate(
                test_result.test_execution.artefact_build.artefact
            )
            artefact_build_response = ArtefactBuildMinimalResponse.model_validate(
                test_result.test_execution.artefact_build
            )

            # Create the context object with all the nested data
            enhanced_result = TestResultResponseWithContext(
                test_result=test_result_response,
                test_execution=test_execution_response,
                artefact=artefact_response,
                artefact_build=artefact_build_response,
            )
            enhanced_results.append(enhanced_result)

        return TestResultSearchResponseWithContext(
            count=total_count, test_results=enhanced_results
        )
    else:
        return TestResultSearchResponseWithContext(count=0, test_results=[])
