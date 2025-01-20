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

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from test_observer.data_access.models import (
    ArtefactBuild,
    TestExecution,
    TestExecutionRerunRequest,
    Artefact,
)
from test_observer.data_access.repository import get_or_create
from test_observer.data_access.setup import get_db

from .models import DeleteReruns, PendingRerun, RerunRequest

router = APIRouter()


@router.post("/reruns", response_model=list[PendingRerun])
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

    return get_or_create(db, TestExecutionRerunRequest, {"test_execution_id": te.id})


@router.get("/reruns", response_model=list[PendingRerun])
def get_rerun_requests(db: Session = Depends(get_db)):
    return db.scalars(
        select(TestExecutionRerunRequest).options(
            joinedload(TestExecutionRerunRequest.test_execution)
            .joinedload(TestExecution.artefact_build)
            .joinedload(ArtefactBuild.artefact)
            .joinedload(Artefact.assignee),
            joinedload(TestExecutionRerunRequest.test_execution).joinedload(
                TestExecution.environment
            ),
        )
    )


@router.delete("/reruns")
def delete_rerun_requests(request: DeleteReruns, db: Session = Depends(get_db)):
    db.execute(
        delete(TestExecutionRerunRequest).where(
            TestExecutionRerunRequest.test_execution_id.in_(request.test_execution_ids)
        )
    )
    db.commit()


class _TestExecutionNotFound(ValueError):
    ...
