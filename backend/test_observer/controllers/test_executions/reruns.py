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


import contextlib

from fastapi import APIRouter, Depends, HTTPException, Response, status, Security
from sqlalchemy import delete, select, asc, tuple_
from sqlalchemy.orm import Session, selectinload

from test_observer.common.permissions import Permission, permission_checker
from test_observer.data_access.models import (
    ArtefactBuild,
    Environment,
    TestExecution,
    TestExecutionRerunRequest,
    Artefact,
    FamilyName,
)
from test_observer.data_access.repository import get_or_create
from test_observer.data_access.setup import get_db

from .models import DeleteReruns, PendingRerun, RerunRequest

router = APIRouter()


@router.post(
    "/reruns",
    response_model=list[PendingRerun],
    dependencies=[Security(permission_checker, scopes=[Permission.change_rerun])],
)
def create_rerun_requests(
    request: RerunRequest, response: Response, db: Session = Depends(get_db)
):
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
    dependencies=[Security(permission_checker, scopes=[Permission.change_rerun])],
)
def delete_rerun_requests(request: DeleteReruns, db: Session = Depends(get_db)):
    # Delete rerun requests matching any of the test executions in a single query
    # Using tuple comparison to match the composite key
    subquery = select(
        TestExecution.test_plan_id,
        TestExecution.artefact_build_id,
        TestExecution.environment_id,
    ).where(TestExecution.id.in_(request.test_execution_ids))

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


class _TestExecutionNotFound(ValueError): ...
