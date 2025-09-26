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
    desc,
    select,
)
from sqlalchemy.orm import Session, selectinload
from typing import Annotated
import urllib

from test_observer.data_access.models import (
    ArtefactBuild,
    TestExecution,
    TestResult,
    TestExecutionMetadata,
)
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.setup import get_db
from .models import (
    TestResultSearchResponseWithContext,
    TestResultResponseWithContext,
    TestResultSearchFilters,
)
from test_observer.controllers.execution_metadata.models import ExecutionMetadata
from .filter_test_results import filter_test_results

router = APIRouter(tags=["test-results"])


def parse_execution_metadata(
    execution_metadata: list[str] | None = Query(
        None,
        description=(
            "Filter by execution metadata (category:value). "
            "Category and value must be percent encoded."
        ),
    ),
) -> ExecutionMetadata | None:
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
        result.append(
            TestExecutionMetadata(
                category=urllib.parse.unquote(category),
                value=urllib.parse.unquote(value),
            )
        )
    return ExecutionMetadata.from_rows(result)


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
        ExecutionMetadata | None, Depends(parse_execution_metadata)
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
        int, Query(ge=0, le=1000, description="Maximum number of results to return")
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
    # Build the filters
    filters = TestResultSearchFilters(
        families=families or [],
        environments=environments or [],
        test_cases=test_cases or [],
        template_ids=template_ids or [],
        execution_metadata=execution_metadata or ExecutionMetadata(),
        issues=issues or [],
        from_date=from_date,
        until_date=until_date,
        limit=limit,
        offset=offset,
    )

    # Run paginated query
    pagination_query = select(TestResult)
    paginated_query = filter_test_results(pagination_query, filters)
    paginated_query = paginated_query.order_by(
        desc(TestExecution.created_at), desc(TestResult.id)
    )
    pagination_query = pagination_query.options(
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
    test_results = db.execute(paginated_query).scalars().all()

    # Run count query
    count_query = select(func.count()).select_from(TestResult)
    count_filters = filters.model_copy(update={"limit": None, "offset": None})
    count_query = filter_test_results(count_query, count_filters)
    total_count = db.execute(count_query).scalar()

    # Return results
    return TestResultSearchResponseWithContext(
        count=total_count or 0,
        test_results=[
            TestResultResponseWithContext(
                test_result=tr,
                test_execution=tr.test_execution,
                artefact=tr.test_execution.artefact_build.artefact,
                artefact_build=tr.test_execution.artefact_build,
            )
            for tr in test_results
        ],
    )
