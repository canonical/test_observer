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

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Security
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.common.permissions import Permission, permission_checker
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    TestCase,
    TestExecution,
    TestResult,
)
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.setup import get_db

from . import reported_issues
from .models import TestCasesResponse

router = APIRouter(tags=["test-cases"])
router.include_router(reported_issues.router)


@router.get(
    "",
    response_model=TestCasesResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_test])],
)
def get_test_cases(
    q: Annotated[
        str | None,
        Query(description="Search term for test case names"),
    ] = None,
    families: Annotated[
        list[FamilyName] | None,
        Query(description="Filter by artefact families"),
    ] = None,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=1000,
            description="Maximum number of results (defaults to 50 if not specified)",
        ),
    ] = 50,
    offset: Annotated[
        int,
        Query(ge=0, description="Number of results to skip for pagination"),
    ] = 0,
    db: Session = Depends(get_db),
) -> TestCasesResponse:
    """
    Returns test cases as a flat list with their template IDs.

    Template ID represents the generic test (e.g., "disk/stats_name")
    Test case name is the specific instance (e.g., "disk/stats_nvme0n1")
    Multiple test cases can share the same template ID but have different names.
    """
    query = (
        select(
            TestCase.name.label("test_case"),
            TestCase.template_id,
        )
        .distinct()
        .order_by(TestCase.name, TestCase.template_id)
    )

    # Filter by families if provided
    if families and len(families) > 0:
        query = (
            query.join(TestResult, TestResult.test_case_id == TestCase.id)
            .join(TestExecution, TestExecution.id == TestResult.test_execution_id)
            .join(ArtefactBuild, ArtefactBuild.id == TestExecution.artefact_build_id)
            .join(Artefact, Artefact.id == ArtefactBuild.artefact_id)
            .where(Artefact.family.in_(families))
        )

    # Apply search filter if provided
    if q and q.strip():
        search_term = f"%{q.strip()}%"
        query = query.where(TestCase.name.ilike(search_term))

    # Apply pagination
    query = query.offset(offset).limit(limit)

    rows = db.execute(query).mappings().all()
    return TestCasesResponse.from_rows(rows)
