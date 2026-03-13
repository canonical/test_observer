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

from datetime import datetime
from typing import Annotated, Literal, TypeVar

from fastapi import APIRouter, Depends, Query, Security
from sqlalchemy import Select, and_, desc, exists, func, select
from sqlalchemy.orm import Session, selectinload

from test_observer.common.constants import QueryValue
from test_observer.common.permissions import Permission, permission_checker
from test_observer.controllers.execution_metadata.models import ExecutionMetadata
from test_observer.controllers.test_results.filter_test_results import filter_test_results
from test_observer.controllers.test_results.shared_models import TestResultSearchFilters
from test_observer.controllers.test_results.test_results import parse_execution_metadata, parse_list_or_query_value
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    TestExecution,
    TestExecutionRerunRequest,
    TestResult,
)
from test_observer.data_access.models_enums import FamilyName, TestExecutionStatus, TestResultStatus
from test_observer.data_access.setup import get_db

from .models import TestExecutionSearchItem, TestExecutionSearchResponse
from .test_execution import TEST_EXECUTION_OPTIONS

router = APIRouter(tags=["test-executions"])

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


def _search_with_results(
    filters: TestResultSearchFilters,
    test_result_ids: list[int],
    db: Session,
) -> tuple[list[TestResult], int]:
    """Query test results using the shared filter machinery."""
    data_query = select(TestResult).options(*_TEST_RESULT_QUERY_OPTIONS)
    data_query = filter_test_results(data_query, filters)
    if test_result_ids:
        data_query = data_query.where(TestResult.id.in_(test_result_ids))
    data_query = data_query.order_by(desc(TestResult.created_at), desc(TestResult.id))

    count_filters = filters.model_copy(update={"limit": None, "offset": None})
    count_query = select(func.count()).select_from(TestResult)
    count_query = filter_test_results(count_query, count_filters)
    if test_result_ids:
        count_query = count_query.where(TestResult.id.in_(test_result_ids))

    rows = db.execute(data_query).scalars().all()
    total = db.execute(count_query).scalar() or 0
    return list(rows), total


def _build_no_result_filters(
    filters: TestResultSearchFilters,
) -> tuple[list, set[str]]:
    """Build SQLAlchemy filter expressions for execution-level criteria.

    Only applies filters that are meaningful when there are no test results
    (i.e. skips test-result-level filters such as test_cases, template_ids,
    issues, test_result_statuses, from_date, until_date).
    """
    from sqlalchemy.orm import aliased

    from test_observer.controllers.test_results.filter_test_results import filter_execution_metadata

    query_filters = []
    joins_needed: set[str] = set()

    # Must have no test results
    query_filters.append(
        ~exists(select(1).select_from(TestResult).where(TestResult.test_execution_id == TestExecution.id))
    )

    if filters.families:
        query_filters.append(Artefact.family.in_(filters.families))
        joins_needed.update(["artefact_build", "artefact"])

    if filters.artefacts:
        query_filters.append(Artefact.name.in_(filters.artefacts))
        joins_needed.update(["artefact_build", "artefact"])

    if filters.artefact_is_archived is not None:
        query_filters.append(Artefact.archived == filters.artefact_is_archived)
        joins_needed.update(["artefact_build", "artefact"])

    if filters.environments:
        query_filters.append(Environment.name.in_(filters.environments))
        joins_needed.add("environment")

    if filters.execution_metadata and len(filters.execution_metadata) > 0:
        query_filters.append(filter_execution_metadata(filters.execution_metadata))

    if filters.test_execution_statuses:
        query_filters.append(TestExecution.status.in_(filters.test_execution_statuses))

    if filters.assignee_ids != []:
        if filters.assignee_ids == QueryValue.ANY:
            query_filters.append(Artefact.assignee_id.isnot(None))
        elif filters.assignee_ids == QueryValue.NONE:
            query_filters.append(Artefact.assignee_id.is_(None))
        elif isinstance(filters.assignee_ids, list) and filters.assignee_ids:
            query_filters.append(Artefact.assignee_id.in_(filters.assignee_ids))
        joins_needed.update(["artefact_build", "artefact"])

    if filters.rerun_is_requested is not None:
        rerun_exists = exists(
            select(1)
            .select_from(TestExecutionRerunRequest)
            .where(
                TestExecutionRerunRequest.test_plan_id == TestExecution.test_plan_id,
                TestExecutionRerunRequest.artefact_build_id == TestExecution.artefact_build_id,
                TestExecutionRerunRequest.environment_id == TestExecution.environment_id,
            )
        )
        query_filters.append(rerun_exists if filters.rerun_is_requested else ~rerun_exists)

    if filters.execution_is_latest is not None:
        newer_execution = aliased(TestExecution)
        newer_execution_exists = exists(
            select(1)
            .select_from(newer_execution)
            .where(
                TestExecution.test_plan_id == newer_execution.test_plan_id,
                TestExecution.artefact_build_id == newer_execution.artefact_build_id,
                TestExecution.environment_id == newer_execution.environment_id,
                TestExecution.id < newer_execution.id,
            )
        )
        query_filters.append(~newer_execution_exists if filters.execution_is_latest else newer_execution_exists)

    return query_filters, joins_needed


def _apply_te_joins(query: Select, joins_needed: set[str]) -> Select:
    if "artefact_build" in joins_needed:
        query = query.join(TestExecution.artefact_build)
    if "artefact" in joins_needed:
        query = query.join(ArtefactBuild.artefact)
    if "environment" in joins_needed:
        query = query.join(TestExecution.environment)
    return query


def _search_without_results(
    filters: TestResultSearchFilters,
    db: Session,
) -> tuple[list[TestExecution], int]:
    """Query test executions that have no test results."""
    query_filters, joins_needed = _build_no_result_filters(filters)

    data_query = select(TestExecution).options(*TEST_EXECUTION_OPTIONS)
    data_query = _apply_te_joins(data_query, joins_needed)
    if query_filters:
        data_query = data_query.where(and_(*query_filters))
    data_query = data_query.order_by(desc(TestExecution.created_at), desc(TestExecution.id))
    if filters.offset is not None:
        data_query = data_query.offset(filters.offset)
    if filters.limit is not None:
        data_query = data_query.limit(filters.limit)

    count_query = select(func.count()).select_from(TestExecution)
    count_query = _apply_te_joins(count_query, joins_needed)
    if query_filters:
        count_query = count_query.where(and_(*query_filters))

    rows = db.execute(data_query).scalars().all()
    total = db.execute(count_query).scalar() or 0
    return list(rows), total


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
        Query(description="Filter by issue IDs attached to test results"),
    ] = None,
    test_result_statuses: Annotated[
        list[TestResultStatus] | None,
        Query(description="Filter by test result statuses"),
    ] = None,
    test_execution_statuses: Annotated[
        list[TestExecutionStatus] | None,
        Query(description="Filter by test execution statuses"),
    ] = None,
    assignee_ids: Annotated[
        list[int] | list[Literal[QueryValue.ANY]] | list[Literal[QueryValue.NONE]] | None,
        Query(description="Filter by assignee user ids"),
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
    from_date: Annotated[datetime | None, Query(description="Filter results from this timestamp")] = None,
    until_date: Annotated[datetime | None, Query(description="Filter results until this timestamp")] = None,
    test_result: Annotated[
        list[int] | list[Literal[QueryValue.ANY]] | list[Literal[QueryValue.NONE]] | None,
        Query(
            description=(
                "Filter by test result presence: 'any' (executions with results), "
                "'none' (executions without results), or specific test result ID(s)"
            )
        ),
    ] = None,
    limit: Annotated[int, Query(ge=0, le=1000, description="Maximum number of results to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of results to skip for pagination")] = 0,
    db: Session = Depends(get_db),
) -> TestExecutionSearchResponse:
    """Search test executions with optional test result context.

    Returns at least one item per matching test execution:
    - If the execution has no relevant test results, test_result is null.
    - Otherwise one item per test result (as in GET /v1/test-results).

    Use test_result=none to find executions without results,
    test_result=any to find executions with results,
    or test_result={id} to filter by specific test result IDs.
    """
    parsed_test_result = parse_list_or_query_value(test_result)  # type: ignore[misc]

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
        assignee_ids=parse_list_or_query_value(assignee_ids),  # type: ignore[arg-type]
        rerun_is_requested=rerun_is_requested,
        execution_is_latest=execution_is_latest,
        from_date=from_date,
        until_date=until_date,
        limit=limit,
        offset=offset,
    )

    if parsed_test_result == QueryValue.NONE:
        test_executions, total = _search_without_results(filters, db)
        items = [
            TestExecutionSearchItem.model_validate(
                {
                    "test_execution": te,
                    "test_result": None,
                    "artefact": te.artefact_build.artefact,
                    "artefact_build": te.artefact_build,
                }
            )
            for te in test_executions
        ]
    else:
        specific_ids: list[int] = (
            [] if not isinstance(parsed_test_result, list) else parsed_test_result  # type: ignore[assignment]
        )
        test_results, total = _search_with_results(filters, specific_ids, db)
        items = [
            TestExecutionSearchItem.model_validate(
                {
                    "test_execution": tr.test_execution,
                    "test_result": tr,
                    "artefact": tr.test_execution.artefact_build.artefact,
                    "artefact_build": tr.test_execution.artefact_build,
                }
            )
            for tr in test_results
        ]

    return TestExecutionSearchResponse(
        count=total,
        limit=limit,
        offset=offset,
        test_executions=items,
    )
