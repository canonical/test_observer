# Copyright 2025 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import base64
from datetime import datetime
from typing import Annotated, Literal, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from sqlalchemy import (
    desc,
    func,
    select,
)
from sqlalchemy.orm import Session, selectinload

from test_observer.common.constants import QueryValue
from test_observer.common.enums import Permission
from test_observer.common.permissions import permission_checker
from test_observer.controllers.execution_metadata.models import ExecutionMetadata
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    IssueTestResultAttachment,
    IssueTestResultAttachmentRule,
    TestExecution,
    TestExecutionMetadata,
    TestResult,
)
from test_observer.data_access.models_enums import (
    FamilyName,
    TestExecutionStatus,
    TestResultStatus,
)
from test_observer.data_access.setup import get_db

from .filter_test_results import filter_test_results
from .models import (
    TestResultResponseWithContext,
    TestResultSearchResponseWithContext,
)
from .shared_models import TestResultSearchFilters

router = APIRouter(tags=["test-results"])

T = TypeVar("T")


def parse_execution_metadata(
    execution_metadata: list[str] | None = Query(
        None,
        description=("Filter by execution metadata (base64 encoded category:value pairs)."),
    ),
) -> ExecutionMetadata | None:
    if execution_metadata is None:
        return None
    result = []
    for item in execution_metadata:
        colon_index = item.find(":")

        if colon_index == -1:
            raise HTTPException(
                status_code=422,
                detail=(f"Invalid execution metadata format: '{item}'. Expected base64 encoded 'category:value'."),
            )

        try:
            category = base64.b64decode(item[:colon_index]).decode("utf-8")
            value = base64.b64decode(item[colon_index + 1 :]).decode("utf-8")
        except ValueError as e:
            raise HTTPException(
                status_code=422,
                detail=(f"Invalid base64 encoding in execution metadata: '{item}'."),
            ) from e

        if not category or not value:
            raise HTTPException(
                status_code=422,
                detail=(f"Invalid execution metadata format: '{item}'. Both category and value must be non-empty."),
            )

        result.append(
            TestExecutionMetadata(
                category=category,
                value=value,
            )
        )

    return ExecutionMetadata.from_rows(result)


def parse_list_or_query_value(
    input: list[T] | list[QueryValue] | None,
) -> list[T] | QueryValue:
    """
    Parse a list that may contain integers or QueryValue literals.

    Returns:
    - Empty list if input is None
    - The last QueryValue (mimicking FastAPI behavior)
    - The list of items otherwise
    """
    if input is None:
        return []
    if len(input) > 0 and all(item in QueryValue for item in input):
        return input[-1]  # type: ignore[return-value]
    return input  # type: ignore[return-value]


def _search_with_result_details(
    filters: TestResultSearchFilters,
    db: Session,
) -> tuple[list[TestResult], int]:
    """Query test results with full details using shared filter machinery."""
    _artefact = (
        selectinload(TestResult.test_execution)
        .selectinload(TestExecution.artefact_build)
        .selectinload(ArtefactBuild.artefacts)
    )
    query = select(TestResult).options(
        selectinload(TestResult.test_case),
        selectinload(TestResult.test_execution).selectinload(TestExecution.environment),
        _artefact.selectinload(Artefact.reviewers),
        selectinload(TestResult.test_execution).selectinload(TestExecution.execution_metadata),
        selectinload(TestResult.test_execution).selectinload(TestExecution.test_plan),
        selectinload(TestResult.test_execution).selectinload(TestExecution.relevant_links),
        selectinload(TestResult.test_execution).selectinload(TestExecution.rerun_request),
        selectinload(TestResult.issue_attachments).selectinload(IssueTestResultAttachment.issue),
        selectinload(TestResult.issue_attachments)
        .selectinload(IssueTestResultAttachment.attachment_rule)
        .selectinload(IssueTestResultAttachmentRule.execution_metadata),
        # Pre-load all builds + environment reviews for each artefact
        # so that Artefact.all_environment_reviews_count and completed_environment_reviews_count
        # can evaluate without additional queries
        _artefact.selectinload(Artefact.builds).selectinload(ArtefactBuild.environment_reviews),
    )
    query = filter_test_results(query, filters)
    query = query.order_by(desc(TestResult.created_at), desc(TestResult.id))
    if filters.offset is not None:
        query = query.offset(filters.offset)
    if filters.limit is not None:
        query = query.limit(filters.limit)

    count_filters = filters.model_copy(update={"limit": None, "offset": None})
    count_query = select(func.count()).select_from(TestResult)
    count_query = filter_test_results(count_query, count_filters)

    rows = db.execute(query).scalars().all()
    total = db.execute(count_query).scalar() or 0
    return list(rows), total


@router.get(
    "",
    response_model=TestResultSearchResponseWithContext,
    dependencies=[Security(permission_checker, scopes=[Permission.view_test])],
)
def search_test_results(
    families: Annotated[
        list[FamilyName] | None,
        Query(description="Filter by artefact families (e.g., charm,snap)"),
    ] = None,
    artefacts: Annotated[
        list[str] | None,
        Query(description="Filter by artefact names"),
    ] = None,
    artefact_is_archived: Annotated[
        bool | None,
        Query(description="Filter by whether the artefact is archived"),
    ] = None,
    environments: Annotated[
        list[str] | None,
        Query(description="Filter by environment names"),
    ] = None,
    test_cases: Annotated[
        list[str] | None,
        Query(description="Filter by test case names"),
    ] = None,
    template_ids: Annotated[list[str] | None, Query(description="Filter by template IDs")] = None,
    execution_metadata: Annotated[ExecutionMetadata | None, Depends(parse_execution_metadata)] = None,
    issues: Annotated[
        list[int] | list[Literal[QueryValue.ANY]] | list[Literal[QueryValue.NONE]] | None,
        Query(description="Filter by issue IDs"),
    ] = None,
    test_result_statuses: Annotated[
        list[TestResultStatus] | None,
        Query(description="Filter by test result statuses"),
    ] = None,
    test_execution_statuses: Annotated[
        list[TestExecutionStatus] | None,
        Query(description="Filter by test execution statuses"),
    ] = None,
    reviewer_ids: Annotated[
        list[int] | list[Literal[QueryValue.ANY]] | list[Literal[QueryValue.NONE]] | None,
        Query(description="Filter by reviewer user ids"),
    ] = None,
    assignee_ids: Annotated[
        list[int] | list[Literal[QueryValue.ANY]] | list[Literal[QueryValue.NONE]] | None,
        Query(description="DEPRECATED: Use reviewer_ids instead", deprecated=True),
    ] = None,
    rerun_is_requested: Annotated[
        bool | None,
        Query(description=("Filter by whether a rerun has been requested for the test execution")),
    ] = None,
    execution_is_latest: Annotated[
        bool | None,
        Query(
            description=(
                "Filter by whether the test execution is the latest in its environment/artifact/test plan combination"
            )
        ),
    ] = None,
    from_date: Annotated[datetime | None, Query(description="Filter results from this timestamp")] = None,
    until_date: Annotated[datetime | None, Query(description="Filter results until this timestamp")] = None,
    limit: Annotated[int, Query(ge=0, le=1000, description="Maximum number of results to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of results to skip for pagination")] = 0,
    db: Session = Depends(get_db),
) -> TestResultSearchResponseWithContext:
    """
    Search test results across artefacts using flexible filters.

    Returns one item per matching test result with execution, artefact, and build context.
    """
    filters = TestResultSearchFilters(
        families=families or [],
        artefacts=artefacts or [],
        artefact_is_archived=artefact_is_archived,
        environments=environments or [],
        test_cases=test_cases or [],
        template_ids=template_ids or [],
        execution_metadata=execution_metadata or ExecutionMetadata(),
        issues=parse_list_or_query_value(issues),  # type: ignore[arg-type]
        test_result_statuses=test_result_statuses or [],
        test_execution_statuses=test_execution_statuses or [],
        reviewer_ids=parse_list_or_query_value(reviewer_ids),  # type: ignore[arg-type]
        assignee_ids=parse_list_or_query_value(assignee_ids),  # type: ignore[arg-type]
        rerun_is_requested=rerun_is_requested,
        execution_is_latest=execution_is_latest,
        from_date=from_date,
        until_date=until_date,
        limit=limit,
        offset=offset,
    )

    test_results, total = _search_with_result_details(filters, db)

    return TestResultSearchResponseWithContext(
        count=total,
        limit=limit,
        offset=offset,
        test_results=[
            TestResultResponseWithContext.model_validate(
                {
                    "test_result": tr,
                    "test_execution": tr.test_execution,
                    "artefact": tr.test_execution.artefact_build.artefact,
                    "artefact_build": tr.test_execution.artefact_build,
                }
            )
            for tr in test_results
        ],
    )
