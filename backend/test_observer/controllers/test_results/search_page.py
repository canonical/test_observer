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

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Security
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
from test_observer.data_access.setup import get_db

from .search_page_models import (
    SearchPageArtefact,
    SearchPageArtefactBuild,
    SearchPageEnvironment,
    SearchPageTestExecution,
    SearchPageTestResult,
    TestResultSearchPage,
    TestResultSearchPageRow,
)

router = APIRouter(tags=["test-results"])


@router.get(
    "/search-page",
    response_model=TestResultSearchPage,
    dependencies=[Security(permission_checker, scopes=[Permission.view_test])],
)
def get_test_results_search_page(
    limit: Annotated[
        int,
        Query(ge=1, le=MAX_RESULT_PAGE_LIMIT, description="Maximum number of results to return"),
    ] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of results to skip")] = 0,
    include_count: Annotated[
        bool,
        Query(description="Include the exact total count; null is returned when false"),
    ] = True,
    db: Session = Depends(get_db),
) -> TestResultSearchPage:
    """Return a bounded page of compact test-result data, newest result first.

    ``count`` is exact and independent of the requested page. It is null when
    ``include_count`` is false.
    """
    count = None
    if include_count:
        count = db.execute(select(func.count()).select_from(TestResult)).scalar_one()

    stmt = (
        select(TestResult)
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
        .offset(offset)
        .limit(limit)
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
