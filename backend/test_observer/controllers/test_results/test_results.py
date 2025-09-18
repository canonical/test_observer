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
    func,
    select,
)
from sqlalchemy.orm import Session, selectinload
from typing import Annotated
import urllib

from test_observer.data_access.models import (
    ArtefactBuild,
    TestExecution,
    TestResult,
)
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.setup import get_db
from .models import (
    TestResultSearchResponseWithContext,
    TestResultResponseWithContext,
    TestResultSearchFilters,
)
from test_observer.controllers.test_executions.models import (
    TestResultResponse,
    TestExecutionResponse,
)
from test_observer.controllers.artefacts.models import (
    ArtefactResponse,
    ArtefactBuildMinimalResponse,
)
from .test_results_search import filter_test_results

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

    # Build select query
    query = select(TestResult, func.count().over().label("total_count"))

    # Apply necessary eager loading
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

    # Apply filters
    query = filter_test_results(
        query,
        TestResultSearchFilters(
            families=families,
            environments=environments,
            test_cases=test_cases,
            template_ids=template_ids,
            execution_metadata=execution_metadata,
            issues=issues,
            from_date=from_date,
            until_date=until_date,
            limit=limit,
            offset=offset,
        ),
    )

    # Execute query
    result = db.execute(query).all()

    # Process and return results
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
