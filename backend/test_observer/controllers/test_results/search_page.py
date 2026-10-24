# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Security
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, load_only, selectinload

from test_observer.common.config import MAX_RESULT_PAGE_LIMIT
from test_observer.common.constants import QueryValue
from test_observer.common.enums import Permission
from test_observer.common.permissions import permission_checker
from test_observer.controllers.execution_metadata.models import ExecutionMetadata
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    Issue,
    IssueTestResultAttachment,
    TestCase,
    TestExecution,
    TestExecutionMetadata,
    TestExecutionRerunRequest,
    TestPlan,
    TestResult,
)
from test_observer.data_access.models_enums import (
    FamilyName,
    TestExecutionStatus,
    TestResultStatus,
)
from test_observer.data_access.setup import get_db

from .filter_test_results import filter_test_results
from .search_page_models import (
    SearchPageDetailsArtefact,
    SearchPageDetailsArtefactBuild,
    SearchPageDetailsIssue,
    SearchPageDetailsIssueAttachment,
    SearchPageDetailsResponse,
    SearchPageDetailsTestExecution,
    SearchPageDetailsTestResult,
    SearchPageTableArtefact,
    SearchPageTableArtefactBuild,
    SearchPageTableEnvironment,
    SearchPageTableResponse,
    SearchPageTableRow,
    SearchPageTableTestExecution,
    SearchPageTableTestResult,
)
from .shared_models import TestResultSearchFilters
from .test_results import parse_execution_metadata, parse_list_or_query_value

router = APIRouter(tags=["test-results-search-page"])


def _search_page_results(
    filters: TestResultSearchFilters,
    db: Session,
    include_count: bool,
) -> tuple[list[TestResult], int | None]:
    """Load only table fields and relationships for the requested result block."""
    execution = selectinload(TestResult.test_execution).load_only(
        TestExecution.id,
        TestExecution.status,
        TestExecution.environment_id,
        TestExecution.test_plan_id,
        TestExecution.artefact_build_id,
    )
    artefact_build = execution.selectinload(TestExecution.artefact_build).load_only(
        ArtefactBuild.id,
        ArtefactBuild.architecture,
        ArtefactBuild.artefact_id,
    )
    artefact = artefact_build.selectinload(ArtefactBuild.artefact).load_only(
        Artefact.id,
        Artefact.name,
        Artefact.version,
        Artefact.track,
        Artefact.family,
    )
    query = select(TestResult).options(
        load_only(
            TestResult.id,
            TestResult.status,
            TestResult.created_at,
            TestResult.test_execution_id,
            TestResult.test_case_id,
        ),
        selectinload(TestResult.test_case).load_only(
            TestCase.id,
            TestCase.name,
            TestCase.category,
            TestCase.template_id,
        ),
        execution,
        execution.selectinload(TestExecution.environment).load_only(
            Environment.id,
            Environment.name,
        ),
        execution.selectinload(TestExecution.test_plan).load_only(
            TestPlan.id,
            TestPlan.name,
        ),
        execution.selectinload(TestExecution.rerun_request).load_only(TestExecutionRerunRequest.id),
        execution.selectinload(TestExecution.execution_metadata).load_only(
            TestExecutionMetadata.id,
            TestExecutionMetadata.category,
            TestExecutionMetadata.value,
        ),
        artefact_build,
        artefact,
    )
    query = filter_test_results(query, filters)
    query = query.order_by(desc(TestResult.created_at), desc(TestResult.id))
    if filters.offset is not None:
        query = query.offset(filters.offset)
    if filters.limit is not None:
        query = query.limit(filters.limit)

    rows = db.execute(query).scalars().all()
    count = None
    if include_count:
        count_filters = filters.model_copy(update={"limit": None, "offset": None})
        count_query = select(func.count()).select_from(TestResult)
        count_query = filter_test_results(count_query, count_filters)
        count = db.execute(count_query).scalar() or 0

    return list(rows), count


def _table_row(result: TestResult) -> SearchPageTableRow:
    execution = result.test_execution
    artefact_build = execution.artefact_build
    artefact = artefact_build.artefact
    return SearchPageTableRow(
        test_result=SearchPageTableTestResult(
            id=result.id,
            name=result.test_case.name,
            category=result.test_case.category,
            created_at=result.created_at,
            template_id=result.test_case.template_id,
            status=result.status,
        ),
        test_execution=SearchPageTableTestExecution(
            id=execution.id,
            status=execution.status,
            is_rerun_requested=execution.rerun_request is not None,
            environment=SearchPageTableEnvironment(name=execution.environment.name),
            test_plan=execution.test_plan.name,
            execution_metadata=ExecutionMetadata.from_rows(execution.execution_metadata),
        ),
        artefact=SearchPageTableArtefact(
            id=artefact.id,
            name=artefact.name,
            version=artefact.version,
            track=artefact.track,
            family=artefact.family,
        ),
        artefact_build=SearchPageTableArtefactBuild(architecture=artefact_build.architecture),
    )


@router.get(
    "",
    response_model=SearchPageTableResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_test])],
)
def search_test_results_page(
    families: Annotated[
        list[FamilyName] | None,
        Query(description="Filter by artefact families (e.g., charm,snap)"),
    ] = None,
    artefacts: Annotated[list[str] | None, Query(description="Filter by artefact names")] = None,
    artefact_versions: Annotated[list[str] | None, Query(description="Filter by artefact versions")] = None,
    artefact_stages: Annotated[list[str] | None, Query(description="Filter by artefact stages")] = None,
    artefact_tracks: Annotated[list[str] | None, Query(description="Filter by artefact tracks")] = None,
    artefact_is_archived: Annotated[
        bool | None,
        Query(description="Filter by whether the artefact is archived"),
    ] = None,
    environments: Annotated[list[str] | None, Query(description="Filter by environment names")] = None,
    test_plans: Annotated[list[str] | None, Query(description="Filter by test plan names")] = None,
    test_cases: Annotated[list[str] | None, Query(description="Filter by test case names")] = None,
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
        Query(description="Filter by whether a rerun has been requested for the test execution"),
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
    limit: Annotated[
        int,
        Query(ge=0, le=MAX_RESULT_PAGE_LIMIT, description="Maximum number of results to return"),
    ] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of results to skip for pagination")] = 0,
    include_count: Annotated[
        bool,
        Query(description="Include the exact total count; null is returned when false"),
    ] = True,
    db: Session = Depends(get_db),
) -> SearchPageTableResponse:
    """Return only the fields needed to render a Search table range."""
    filters = TestResultSearchFilters(
        families=families or [],
        artefacts=artefacts or [],
        artefact_versions=artefact_versions or [],
        artefact_stages=artefact_stages or [],
        artefact_tracks=artefact_tracks or [],
        artefact_is_archived=artefact_is_archived,
        environments=environments or [],
        test_cases=test_cases or [],
        template_ids=template_ids or [],
        test_plans=test_plans or [],
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
    test_results, count = _search_page_results(filters, db, include_count)
    return SearchPageTableResponse(
        count=count,
        limit=limit,
        offset=offset,
        rows=[_table_row(result) for result in test_results],
    )


@router.get(
    "/{test_result_id}",
    response_model=SearchPageDetailsResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_test])],
)
def get_search_page_result_details(
    test_result_id: Annotated[int, Path(gt=0)],
    db: Session = Depends(get_db),
) -> SearchPageDetailsResponse:
    """Load only the fields needed by the Search details modal for one result."""
    execution_loader = selectinload(TestResult.test_execution).load_only(
        TestExecution.id,
        TestExecution.status,
        TestExecution.created_at,
        TestExecution.environment_id,
        TestExecution.test_plan_id,
        TestExecution.artefact_build_id,
    )
    artefact_build_loader = execution_loader.selectinload(TestExecution.artefact_build).load_only(
        ArtefactBuild.id,
        ArtefactBuild.architecture,
        ArtefactBuild.artefact_id,
    )
    artefact_loader = artefact_build_loader.selectinload(ArtefactBuild.artefact).load_only(
        Artefact.id,
        Artefact.name,
        Artefact.version,
        Artefact.track,
        Artefact.family,
    )
    result = db.execute(
        select(TestResult)
        .where(TestResult.id == test_result_id)
        .options(
            load_only(
                TestResult.id,
                TestResult.status,
                TestResult.io_log,
                TestResult.test_case_id,
                TestResult.test_execution_id,
            ),
            selectinload(TestResult.test_case).load_only(
                TestCase.id,
                TestCase.name,
                TestCase.category,
                TestCase.template_id,
            ),
            selectinload(TestResult.issue_attachments)
            .load_only(
                IssueTestResultAttachment.id,
                IssueTestResultAttachment.test_result_id,
                IssueTestResultAttachment.issue_id,
            )
            .selectinload(IssueTestResultAttachment.issue)
            .load_only(
                Issue.id,
                Issue.source,
                Issue.project,
                Issue.key,
                Issue.title,
                Issue.status,
            ),
            execution_loader,
            execution_loader.selectinload(TestExecution.environment).load_only(
                Environment.id,
                Environment.name,
            ),
            execution_loader.selectinload(TestExecution.test_plan).load_only(
                TestPlan.id,
                TestPlan.name,
            ),
            execution_loader.selectinload(TestExecution.execution_metadata).load_only(
                TestExecutionMetadata.id,
                TestExecutionMetadata.category,
                TestExecutionMetadata.value,
            ),
            artefact_build_loader,
            artefact_loader,
        )
    ).scalar_one_or_none()
    if result is None:
        raise HTTPException(status_code=404, detail="Test result not found")

    execution = result.test_execution
    artefact_build = execution.artefact_build
    artefact = artefact_build.artefact
    return SearchPageDetailsResponse(
        test_result=SearchPageDetailsTestResult(
            id=result.id,
            name=result.test_case.name,
            category=result.test_case.category,
            template_id=result.test_case.template_id,
            status=result.status,
            io_log=result.io_log,
            issues=[
                SearchPageDetailsIssueAttachment(
                    issue=SearchPageDetailsIssue(
                        id=attachment.issue.id,
                        source=attachment.issue.source,
                        project=attachment.issue.project,
                        key=attachment.issue.key,
                        title=attachment.issue.title,
                        status=attachment.issue.status,
                        url=attachment.issue.url,
                    )
                )
                for attachment in result.issue_attachments
            ],
        ),
        test_execution=SearchPageDetailsTestExecution(
            id=execution.id,
            status=execution.status,
            environment=SearchPageTableEnvironment(name=execution.environment.name),
            test_plan=execution.test_plan.name,
            created_at=execution.created_at,
            execution_metadata=ExecutionMetadata.from_rows(execution.execution_metadata),
        ),
        artefact=SearchPageDetailsArtefact(
            id=artefact.id,
            name=artefact.name,
            version=artefact.version,
            track=artefact.track,
            family=artefact.family,
        ),
        artefact_build=SearchPageDetailsArtefactBuild(architecture=artefact_build.architecture),
    )
