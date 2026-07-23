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
from collections import defaultdict
from datetime import datetime
from typing import Annotated, Literal, TypeVar

from fastapi import Depends, HTTPException, Query, Security
from sqlalchemy import and_, desc, exists, func, select
from sqlalchemy.orm import Session, selectinload

from test_observer.common.constants import QueryValue
from test_observer.common.enums import Permission
from test_observer.common.permissions import permission_checker
from test_observer.controllers.execution_metadata.models import ExecutionMetadata
from test_observer.controllers.test_executions.execution_filters import (
    apply_te_joins,
    build_execution_filters,
)
from test_observer.controllers.test_executions.shared_models import (
    TestExecutionSearchFilters,
    TestResultResponse,
)
from test_observer.data_access.models import (
    ArtefactBuild,
    TestExecution,
    TestExecutionMetadata,
    TestResult,
)
from test_observer.data_access.models_enums import FamilyName, TestExecutionStatus
from test_observer.data_access.setup import get_db

from .models import TestExecutionResponseWithContext, TestExecutionSearchResponse
from .router import router
from .test_execution import TEST_EXECUTION_OPTIONS

T = TypeVar("T")

# selectinload options used when querying from TestResult root (test_result=any/{ids})
_TEST_RESULT_QUERY_OPTIONS = [
    selectinload(TestResult.test_case),
    selectinload(TestResult.test_execution).selectinload(TestExecution.environment),
    selectinload(TestResult.test_execution)
    .selectinload(TestExecution.artefact_build)
    .selectinload(ArtefactBuild.artefact),
    selectinload(TestResult.issue_attachments),
    selectinload(TestResult.test_execution).selectinload(TestExecution.execution_metadata),
    selectinload(TestResult.test_execution).selectinload(TestExecution.relevant_links),
    selectinload(TestResult.test_execution).selectinload(TestExecution.rerun_request),
    selectinload(TestResult.test_execution).selectinload(TestExecution.test_plan),
    selectinload(TestResult.test_execution)
    .selectinload(TestExecution.test_results)
    .selectinload(TestResult.issue_attachments),
]


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
    if input is None:
        return []

    parsed_query_values = []
    for item in input:
        if isinstance(item, QueryValue):
            parsed_query_values.append(item)
            continue
        if isinstance(item, str):
            try:
                parsed_query_values.append(QueryValue(item))
                continue
            except ValueError:
                pass

    if parsed_query_values:
        if len(parsed_query_values) != len(input):
            raise HTTPException(
                status_code=422,
                detail=("Cannot combine reserved values 'any'/'none' with specific filter values."),
            )
        return parsed_query_values[-1]

    return input  # type: ignore[return-value]


def _search_executions(
    filters: TestExecutionSearchFilters,
    parsed_test_result: list[int] | QueryValue,
    db: Session,
) -> tuple[list[TestExecution], dict[int, list[TestResult]], int]:
    """Query test executions with a single path for any/none/specific result modes."""
    query_filters, joins_needed = build_execution_filters(filters)

    if parsed_test_result == QueryValue.NONE:
        query_filters.append(
            ~exists(select(1).select_from(TestResult).where(TestResult.test_execution_id == TestExecution.id))
        )
    elif parsed_test_result == QueryValue.ANY:
        query_filters.append(
            exists(select(1).select_from(TestResult).where(TestResult.test_execution_id == TestExecution.id))
        )
    elif isinstance(parsed_test_result, list) and parsed_test_result:
        query_filters.append(
            exists(
                select(1)
                .select_from(TestResult)
                .where(
                    TestResult.test_execution_id == TestExecution.id,
                    TestResult.id.in_(parsed_test_result),
                )
            )
        )
    else:
        query_filters.append(
            exists(select(1).select_from(TestResult).where(TestResult.test_execution_id == TestExecution.id))
        )

    ids_query = select(TestExecution.id)
    ids_query = apply_te_joins(ids_query, joins_needed)
    if query_filters:
        ids_query = ids_query.where(and_(*query_filters))

    ids_query = ids_query.order_by(desc(TestExecution.created_at), desc(TestExecution.id))
    if filters.offset is not None:
        ids_query = ids_query.offset(filters.offset)
    if filters.limit is not None:
        ids_query = ids_query.limit(filters.limit)

    count_query = select(func.count()).select_from(
        apply_te_joins(select(TestExecution.id), joins_needed).where(and_(*query_filters)).subquery()
    )

    execution_ids = [row[0] for row in db.execute(ids_query).all()]
    if not execution_ids:
        total = db.execute(count_query).scalar() or 0
        return [], {}, total

    data_query = select(TestExecution).options(*TEST_EXECUTION_OPTIONS)
    data_query = data_query.where(TestExecution.id.in_(execution_ids))
    rows = db.execute(data_query).scalars().all()

    grouped_results: dict[int, list[TestResult]] = defaultdict(list)
    if parsed_test_result != QueryValue.NONE:
        result_query = select(TestResult).options(*_TEST_RESULT_QUERY_OPTIONS)
        result_query = result_query.where(TestResult.test_execution_id.in_(execution_ids))
        if isinstance(parsed_test_result, list) and parsed_test_result:
            result_query = result_query.where(TestResult.id.in_(parsed_test_result))
        result_query = result_query.order_by(desc(TestResult.created_at), desc(TestResult.id))
        for test_result in db.execute(result_query).scalars().all():
            grouped_results[test_result.test_execution_id].append(test_result)

    execution_by_id = {execution.id: execution for execution in rows}
    ordered_rows = [execution_by_id[execution_id] for execution_id in execution_ids if execution_id in execution_by_id]

    total = db.execute(count_query).scalar() or 0
    return ordered_rows, grouped_results, total


@router.get(
    "",
    response_model=TestExecutionSearchResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_test])],
)
def search_test_executions(
    families: Annotated[
        list[FamilyName] | None,
        Query(description="Filter by artefact families (e.g., charm,snap)"),
    ] = None,
    artefacts: Annotated[
        list[str] | None,
        Query(description="Filter by artefact names"),
    ] = None,
    artefact_versions: Annotated[
        list[str] | None,
        Query(description="Filter by artefact versions"),
    ] = None,
    artefact_stages: Annotated[
        list[str] | None,
        Query(description="Filter by artefact stages"),
    ] = None,
    artefact_tracks: Annotated[
        list[str] | None,
        Query(description="Filter by artefact tracks"),
    ] = None,
    artefact_is_archived: Annotated[
        bool | None,
        Query(description="Filter by whether the artefact is archived"),
    ] = None,
    environments: Annotated[
        list[str] | None,
        Query(description="Filter by environment names"),
    ] = None,
    execution_metadata: Annotated[ExecutionMetadata | None, Depends(parse_execution_metadata)] = None,
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
        Query(description="Filter by whether a rerun has been requested for the test execution"),
    ] = None,
    execution_is_latest: Annotated[
        bool | None,
        Query(
            description=(
                "Filter by whether the test execution is the latest in its environment/artefact/test plan combination"
            )
        ),
    ] = None,
    test_result: Annotated[
        list[int] | list[Literal[QueryValue.ANY]] | list[Literal[QueryValue.NONE]] | None,
        Query(
            description=(
                "Filter by test result presence: 'any' (executions with results), "
                "'none' (executions without results), or specific test result ID(s)"
            )
        ),
    ] = None,
    event_names: Annotated[
        list[str] | list[Literal[QueryValue.ANY]] | list[Literal[QueryValue.NONE]] | None,
        Query(
            description=(
                "Filter by event log: 'any' (executions with any events), "
                "'none' (executions without events), or specific event name(s)"
            )
        ),
    ] = None,
    from_date: Annotated[
        datetime | None,
        Query(description="Filter executions updated on or after this datetime"),
    ] = None,
    until_date: Annotated[
        datetime | None,
        Query(description="Filter executions updated on or before this datetime"),
    ] = None,
    limit: Annotated[int, Query(ge=0, le=1000, description="Maximum number of results to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of results to skip for pagination")] = 0,
    db: Session = Depends(get_db),
) -> TestExecutionSearchResponse:
    """Search test executions with optional test result context.

    Returns one item per matching test execution with paginated results.
    The test_results field contains all filtered test results for that execution.

    Use test_result=none to find executions without results,
    test_result=any to find executions with results,
    or test_result={id} to filter by specific test result IDs.
    """
    parsed_test_result = parse_list_or_query_value(test_result)  # type: ignore[misc]

    filters = TestExecutionSearchFilters(
        families=families or [],
        artefacts=artefacts or [],
        artefact_versions=artefact_versions or [],
        artefact_stages=artefact_stages or [],
        artefact_tracks=artefact_tracks or [],
        artefact_is_archived=artefact_is_archived,
        environments=environments or [],
        execution_metadata=execution_metadata or ExecutionMetadata(),
        test_execution_statuses=test_execution_statuses or [],
        reviewer_ids=parse_list_or_query_value(reviewer_ids),  # type: ignore[arg-type]
        assignee_ids=parse_list_or_query_value(assignee_ids),  # type: ignore[arg-type]
        rerun_is_requested=rerun_is_requested,
        execution_is_latest=execution_is_latest,
        event_names=parse_list_or_query_value(event_names),  # type: ignore[arg-type]
        from_date=from_date,
        until_date=until_date,
        limit=limit,
        offset=offset,
    )

    test_executions, grouped_results, total = _search_executions(filters, parsed_test_result, db)
    items = []
    for test_execution in test_executions:
        filtered_results = grouped_results.get(test_execution.id, [])
        item = TestExecutionResponseWithContext.model_validate(test_execution).model_copy(
            update={"test_results": [TestResultResponse.model_validate(result) for result in filtered_results]}
        )
        items.append(item)

    return TestExecutionSearchResponse(
        count=total,
        limit=limit,
        offset=offset,
        test_executions=items,
    )
