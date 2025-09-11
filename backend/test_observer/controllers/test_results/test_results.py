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
from sqlalchemy import (
    and_,
    desc,
    func,
    select,
    exists,
    values,
    column,
    true,
    ColumnExpressionArgument,
)
from sqlalchemy.orm import Session, selectinload
from typing import Annotated
import urllib

from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    Issue,
    IssueTestResultAttachment,
    TestCase,
    TestExecution,
    TestResult,
    TestExecutionMetadata,
    ColumnElement,
)
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.models import test_execution_metadata_association_table
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


def parse_execution_metadata(
    execution_metadata: list[str] | None = Query(
        None,
        description=(
            "Filter by execution metadata (category:value). "
            "Category and value must be percent encoded."
        ),
    ),
) -> list[tuple[str, str]] | None:
    if execution_metadata is None:
        return None
    result = []
    for item in execution_metadata:
        if item.count(":") != 1:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Invalid execution metadata format: '{item}'. "
                    "Expected 'category:value' with a single colon."
                ),
            )
        category, value = item.split(":")
        result.append((urllib.parse.unquote(category), urllib.parse.unquote(value)))
    return result


def filter_execution_metadata(
    execution_metadata: list[tuple[str, str]],
) -> ColumnElement[bool]:
    # Step 1: Build filter_metadata values table
    # This table contains all (category, value) pairs to filter against.
    filter_metadata = (
        values(
            column("category"),
            column("value"),
        )
        .data(execution_metadata)
        .alias("filter_metadata")
    )

    # Step 2: Build metadata_matches query
    # For each test execution and required (category, value),
    # attempt to find a matching metadata row.
    metadata_matches = (
        select(
            TestExecution.id,
            filter_metadata.c.category,
        )
        .join(filter_metadata, true())
        .outerjoin(
            test_execution_metadata_association_table,
            TestExecution.id
            == test_execution_metadata_association_table.c.test_execution_id,
        )
        .outerjoin(
            TestExecutionMetadata,
            and_(
                test_execution_metadata_association_table.c.test_execution_metadata_id
                == TestExecutionMetadata.id,
                TestExecutionMetadata.category == filter_metadata.c.category,
                TestExecutionMetadata.value == filter_metadata.c.value,
            ),
        )
    )

    # Step 3: Group and filter unmatched categories
    # Group by test execution and category,
    # keeping only those where no matching metadata value exists.
    unmatched_categories = metadata_matches.group_by(
        TestExecution.id,
        filter_metadata.c.category,
    ).having(func.count(TestExecutionMetadata.value) == 0)

    # Step 4: Exclude test executions with unmatched categories
    # Exclude any test execution that has at least one
    # unmatched category.
    exclusion_condition = ~exists(
        select(1)
        .select_from(unmatched_categories.subquery())
        .where(unmatched_categories.c.id == TestExecution.id)
    )

    return exclusion_condition


@router.get("", response_model=TestResultSearchResponseWithContext)
def search_test_results(
    families: Annotated[
        list[FamilyName] | None,
        Query(description="Filter by artefact families (e.g., charm,snap)"),
    ] = None,
    environments: Annotated[
        list[str] | None,
        Query(description="Filter by environment names"),
    ] = None,
    test_cases: Annotated[
        list[str] | None,
        Query(description="Filter by test case names"),
    ] = None,
    template_ids: Annotated[
        list[str] | None, Query(description="Filter by template IDs")
    ] = None,
    execution_metadata: Annotated[
        list[tuple[str, str]] | None, Depends(parse_execution_metadata)
    ] = None,
    issues: Annotated[
        list[int] | None,
        Query(description="Filter by Jira or GitHub issue IDs"),
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

    # Build filters and track which joins are needed
    filters: list[ColumnExpressionArgument[bool]] = []
    joins_needed = set()

    joins_needed.add("test_execution")

    if families:
        filters.append(Artefact.family.in_(families))
        joins_needed.update(["test_execution", "artefact_build", "artefact"])

    if environments:
        filters.append(Environment.name.in_(environments))
        joins_needed.update(["test_execution", "environment"])

    if test_cases:
        filters.append(TestCase.name.in_(test_cases))
        joins_needed.add("test_case")

    if template_ids:
        filters.append(TestCase.template_id.in_(template_ids))
        joins_needed.add("test_case")

    if execution_metadata:
        filters.append(filter_execution_metadata(execution_metadata))
        joins_needed.add("execution_metadata")

    if issues:
        filters.append(
            TestResult.id.in_(
                select(IssueTestResultAttachment.test_result_id)
                .join(IssueTestResultAttachment.issue)
                .where(Issue.id.in_(issues))
            )
        )

    if from_date:
        filters.append(TestExecution.created_at >= from_date)  # type: ignore
        joins_needed.add("test_execution")

    if until_date:
        filters.append(TestExecution.created_at <= until_date)  # type: ignore
        joins_needed.add("test_execution")

    # Build the main query with only necessary joins
    query = select(TestResult, func.count().over().label("total_count"))

    if "test_execution" in joins_needed:
        query = query.join(TestResult.test_execution)

    if "environment" in joins_needed:
        query = query.join(TestExecution.environment)

    if "artefact_build" in joins_needed:
        query = query.join(TestExecution.artefact_build)

    if "artefact" in joins_needed:
        query = query.join(ArtefactBuild.artefact)

    if "test_case" in joins_needed:
        query = query.join(TestResult.test_case)

    if "execution_metadata" in joins_needed:
        query = query.join(TestExecution.execution_metadata)

    query = query.options(
        selectinload(TestResult.test_case),
        selectinload(TestResult.test_execution).selectinload(TestExecution.environment),
        selectinload(TestResult.test_execution)
        .selectinload(TestExecution.artefact_build)
        .selectinload(ArtefactBuild.artefact),
        selectinload(TestResult.issue_attachments),
        selectinload(TestResult.test_execution).selectinload(
            TestExecution.execution_metadata
        ),
    )

    # Apply ordering and pagination
    query = (
        query.order_by(desc(TestExecution.created_at), desc(TestResult.id))
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
