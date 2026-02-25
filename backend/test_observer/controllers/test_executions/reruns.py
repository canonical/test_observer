# Copyright 2024 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import contextlib

from fastapi import APIRouter, Depends, HTTPException, Response, status, Security, Query
from fastapi.security import SecurityScopes
from sqlalchemy import delete, select, asc, tuple_, or_
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.dialects.postgresql import insert as pg_insert
from typing import Annotated

from test_observer.common.permissions import Permission, permission_checker
from test_observer.controllers.applications.application_injection import (
    get_current_application,
)
from test_observer.controllers.test_results.filter_test_results import (
    filter_test_results,
)
from test_observer.data_access.models import (
    Application,
    ArtefactBuild,
    Environment,
    TestExecution,
    TestExecutionRerunRequest,
    TestResult,
    Artefact,
    FamilyName,
    User,
)
from test_observer.data_access.repository import get_or_create
from test_observer.data_access.setup import get_db
from test_observer.users.user_injection import get_current_user

from .models import DeleteReruns, PendingRerun, RerunRequest

router = APIRouter()


def modify_reruns(
    db: Session,
    request: RerunRequest | DeleteReruns,
):
    conditions = []

    # Add condition for direct test execution IDs
    if request.test_execution_ids is not None and len(request.test_execution_ids) > 0:
        conditions.append(TestExecution.id.in_(request.test_execution_ids))

    # Add condition for filtered test results
    if request.test_results_filters is not None:
        filters = request.test_results_filters
        if not filters.has_filters():
            raise HTTPException(
                status_code=422,
                detail="At least one filter must be provided in test_results_filters",
            )
        filtered_ids_query = filter_test_results(
            select(TestResult.test_execution_id).distinct(), filters
        )
        conditions.append(TestExecution.id.in_(filtered_ids_query))

    # Do nothing if no conditions were added
    if not conditions:
        return

    # Build subquery selecting the composite key from TestExecution
    subquery = (
        select(
            TestExecution.test_plan_id,
            TestExecution.artefact_build_id,
            TestExecution.environment_id,
        )
        .where(or_(*conditions))
        .distinct()
    )

    if isinstance(request, RerunRequest):
        db.execute(
            pg_insert(TestExecutionRerunRequest)
            .from_select(
                [
                    "test_plan_id",
                    "artefact_build_id",
                    "environment_id",
                ],
                subquery,
            )
            .on_conflict_do_nothing()
        )
    else:
        db.execute(
            delete(TestExecutionRerunRequest).where(
                tuple_(
                    TestExecutionRerunRequest.test_plan_id,
                    TestExecutionRerunRequest.artefact_build_id,
                    TestExecutionRerunRequest.environment_id,
                ).in_(subquery)
            )
        )

    db.commit()


def require_bulk_permission(
    request: RerunRequest | DeleteReruns,
    security_scopes: SecurityScopes,
    user: User | None = Depends(get_current_user),
    app: Application | None = Depends(get_current_application),
):
    if (
        request.test_execution_ids is not None and len(request.test_execution_ids) > 1
    ) or (request.test_results_filters is not None):
        permission_checker(security_scopes, user, app)


@router.post(
    "/reruns",
    response_model=list[PendingRerun] | None,
    dependencies=[
        Security(permission_checker, scopes=[Permission.change_rerun]),
        Security(require_bulk_permission, scopes=[Permission.change_rerun_bulk]),
    ],
)
def create_rerun_requests(
    request: RerunRequest,
    response: Response,
    silent: Annotated[
        bool,
        Query(
            description=(
                "If true, omit returning created reruns in the response body. "
                "Speeds up bulk operations, as the rerun schema contains a lot of "
                "information and returning many reruns can be slow. "
                "Required when creating reruns with test result filters."
            ),
        ),
    ] = False,
    db: Session = Depends(get_db),
):
    if silent:
        modify_reruns(db, request)
        return

    if request.test_results_filters is not None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Creating rerun requests from test results filters must be done silently",
        )

    rerun_requests = []
    for test_execution_id in request.test_execution_ids:
        with contextlib.suppress(_TestExecutionNotFound):
            rerun_requests.append(_create_rerun_request(test_execution_id, db))

    if not rerun_requests:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Didn't find test executions with provided ids",
        )

    if len(rerun_requests) != len(request.test_execution_ids):
        response.status_code = status.HTTP_207_MULTI_STATUS

    db.commit()

    return rerun_requests


def _create_rerun_request(
    test_execution_id: int, db: Session
) -> TestExecutionRerunRequest:
    te = db.get(TestExecution, test_execution_id)
    if not te:
        raise _TestExecutionNotFound

    return get_or_create(
        db,
        TestExecutionRerunRequest,
        {
            "test_plan_id": te.test_plan_id,
            "artefact_build_id": te.artefact_build_id,
            "environment_id": te.environment_id,
        },
    )


@router.get(
    "/reruns",
    response_model=list[PendingRerun],
    dependencies=[Security(permission_checker, scopes=[Permission.view_rerun])],
)
def get_rerun_requests(
    family: FamilyName | None = None,
    limit: int | None = None,
    environment: str | None = None,
    environment_architecture: str | None = None,
    build_architecture: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = (
        select(TestExecutionRerunRequest)
        .join(TestExecutionRerunRequest.artefact_build)
        .join(ArtefactBuild.artefact)
        .join(TestExecutionRerunRequest.environment)
        .options(
            selectinload(TestExecutionRerunRequest.artefact_build)
            .selectinload(ArtefactBuild.artefact)
            .selectinload(Artefact.assignee),
            selectinload(TestExecutionRerunRequest.environment),
            selectinload(TestExecutionRerunRequest.test_plan),
            selectinload(TestExecutionRerunRequest.test_executions),
        )
        .order_by(asc(TestExecutionRerunRequest.created_at))
    )

    if family is not None:
        stmt = stmt.filter(Artefact.family == family)

    if environment is not None:
        stmt = stmt.filter(Environment.name == environment)

    if build_architecture is not None:
        stmt = stmt.filter(ArtefactBuild.architecture == build_architecture)

    if environment_architecture is not None:
        stmt = stmt.filter(Environment.architecture == environment_architecture)

    if limit is not None:
        stmt = stmt.limit(limit)

    return db.scalars(stmt)


@router.delete(
    "/reruns",
    dependencies=[
        Security(permission_checker, scopes=[Permission.change_rerun]),
        Security(require_bulk_permission, scopes=[Permission.change_rerun_bulk]),
    ],
)
def delete_rerun_requests(request: DeleteReruns, db: Session = Depends(get_db)):
    modify_reruns(db, request)


class _TestExecutionNotFound(ValueError): ...
