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

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Security
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload, load_only, raiseload

from test_observer.common.config import MAX_RESULT_PAGE_LIMIT
from test_observer.common.enums import Permission
from test_observer.common.permissions import permission_checker
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    TestCase,
    TestExecution,
    TestPlan,
    TestResult,
)
from test_observer.data_access.models_enums import TestResultStatus
from test_observer.data_access.setup import get_db

from .filter_test_results import filter_test_results
from .search_page_models import (
    SearchPageArtefact,
    SearchPageArtefactBuild,
    SearchPageEnvironment,
    SearchPageTestExecution,
    SearchPageTestResult,
    TestResultSearchPage,
    TestResultSearchPageRow,
)
from .shared_models import TestResultSearchFilters

router = APIRouter(tags=["test-results"])


@router.get(
    "/search-page",
    response_model=TestResultSearchPage,
    dependencies=[Security(permission_checker, scopes=[Permission.view_test])],
)
def get_test_results_search_page(
    request: Request,
    limit: Annotated[
        int,
        Query(ge=1, le=MAX_RESULT_PAGE_LIMIT, description="Maximum number of results to return"),
    ] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of results to skip")] = 0,
    include_count: Annotated[
        bool,
        Query(description="Include the exact total count; null is returned when false"),
    ] = True,
    families: Annotated[list[str] | None, Query(description="Exact artefact family values; repeat for OR")] = None,
    test_result_statuses: Annotated[
        list[TestResultStatus] | None,
        Query(description="Exact result status values; repeat for OR"),
    ] = None,
    artefacts: Annotated[list[str] | None, Query(description="Exact artefact names; repeat for OR")] = None,
    artefact_versions: Annotated[list[str] | None, Query(description="Exact artefact versions; repeat for OR")] = None,
    artefact_tracks: Annotated[list[str] | None, Query(description="Exact artefact tracks; repeat for OR")] = None,
    environments: Annotated[list[str] | None, Query(description="Exact environment names; repeat for OR")] = None,
    test_cases: Annotated[list[str] | None, Query(description="Exact test case names; repeat for OR")] = None,
    test_plans: Annotated[list[str] | None, Query(description="Exact test plan names; repeat for OR")] = None,
    from_date: Annotated[datetime | None, Query(description="Inclusive UTC lower bound on result created_at")] = None,
    until_date: Annotated[datetime | None, Query(description="Inclusive UTC upper bound on result created_at")] = None,
    db: Session = Depends(get_db),
) -> TestResultSearchPage:
    """Return a bounded, server-filtered page of compact results, newest first.

    Repeated list values are exact-match ORs; distinct filters are ANDed.
    ``count`` is exact and independent of the requested page. It is null when
    ``include_count`` is false. Unsupported query keys and invalid date ranges
    are rejected instead of being silently ignored.
    """
    supported_keys = {
        "limit",
        "offset",
        "include_count",
        "families",
        "test_result_statuses",
        "artefacts",
        "artefact_versions",
        "artefact_tracks",
        "environments",
        "test_cases",
        "test_plans",
        "from_date",
        "until_date",
    }
    unknown_keys = sorted(set(request.query_params.keys()) - supported_keys)
    if unknown_keys:
        raise HTTPException(status_code=422, detail=f"Unsupported query parameter(s): {', '.join(unknown_keys)}")
    for key in ("limit", "offset", "include_count", "from_date", "until_date"):
        if len(request.query_params.getlist(key)) > 1:
            raise HTTPException(status_code=422, detail=f"Provide at most one {key} value")

    def as_utc(value: datetime | None, name: str) -> datetime | None:
        if value is None:
            return None
        if value.utcoffset() is None:
            raise HTTPException(status_code=422, detail=f"{name} must include a UTC offset")
        return value.astimezone(UTC)

    from_utc = as_utc(from_date, "from_date")
    until_utc = as_utc(until_date, "until_date")
    if from_utc is not None and until_utc is not None and from_utc > until_utc:
        raise HTTPException(status_code=422, detail="from_date must not be after until_date")

    list_values = {
        "artefacts": artefacts,
        "artefact_versions": artefact_versions,
        "artefact_tracks": artefact_tracks,
        "environments": environments,
        "test_cases": test_cases,
        "test_plans": test_plans,
    }
    if any(value.strip() == "" for values in list_values.values() for value in (values or [])):
        raise HTTPException(status_code=422, detail="Filter values must not be empty")

    filters = TestResultSearchFilters(
        families=families or [],
        test_result_statuses=test_result_statuses or [],
        artefacts=artefacts or [],
        artefact_versions=artefact_versions or [],
        artefact_tracks=artefact_tracks or [],
        environments=environments or [],
        test_cases=test_cases or [],
        test_plans=test_plans or [],
        from_date=from_utc,
        until_date=until_utc,
    )

    count = None
    count_query = filter_test_results(
        select(func.count()).select_from(TestResult),
        filters.model_copy(update={"offset": None, "limit": None}),
    )
    if include_count:
        count = db.execute(count_query).scalar_one()

    stmt = (
        filter_test_results(
            select(TestResult),
            filters.model_copy(update={"offset": offset, "limit": limit}),
        )
        .options(
            load_only(
                TestResult.id,
                TestResult.created_at,
                TestResult.status,
                TestResult.test_case_id,
                TestResult.test_execution_id,
                raiseload=True,
            ),
            joinedload(TestResult.test_case).load_only(
                TestCase.id,
                TestCase.name,
                TestCase.category,
                raiseload=True,
            ),
            joinedload(TestResult.test_execution)
            .load_only(
                TestExecution.id,
                TestExecution.artefact_build_id,
                TestExecution.environment_id,
                TestExecution.test_plan_id,
                raiseload=True,
            )
            .joinedload(TestExecution.environment)
            .load_only(
                Environment.id,
                Environment.name,
                raiseload=True,
            ),
            joinedload(TestResult.test_execution)
            .joinedload(TestExecution.test_plan)
            .load_only(TestPlan.id, TestPlan.name, raiseload=True),
            joinedload(TestResult.test_execution)
            .joinedload(TestExecution.artefact_build)
            .load_only(
                ArtefactBuild.id,
                ArtefactBuild.artefact_id,
                ArtefactBuild.architecture,
                raiseload=True,
            )
            .joinedload(ArtefactBuild.artefact)
            .load_only(
                Artefact.id,
                Artefact.name,
                Artefact.version,
                Artefact.track,
                Artefact.family,
                raiseload=True,
            ),
            raiseload("*"),
        )
        .order_by(desc(TestResult.created_at), desc(TestResult.id))
    )
    results = db.execute(stmt).scalars().all()

    return TestResultSearchPage(
        count=count,
        limit=limit,
        offset=offset,
        test_results=[
            TestResultSearchPageRow(
                test_result=SearchPageTestResult(
                    id=result.id,
                    created_at=result.created_at,
                    name=result.test_case.name,
                    category=result.test_case.category,
                    status=result.status,
                ),
                test_execution=SearchPageTestExecution(
                    id=result.test_execution.id,
                    environment=SearchPageEnvironment(
                        name=result.test_execution.environment.name,
                    ),
                    test_plan=result.test_execution.test_plan.name,
                ),
                artefact=SearchPageArtefact(
                    id=result.test_execution.artefact_build.artefact.id,
                    name=result.test_execution.artefact_build.artefact.name,
                    version=result.test_execution.artefact_build.artefact.version,
                    track=result.test_execution.artefact_build.artefact.track,
                    family=result.test_execution.artefact_build.artefact.family,
                ),
                artefact_build=SearchPageArtefactBuild(
                    architecture=result.test_execution.artefact_build.architecture,
                ),
            )
            for result in results
        ],
    )
