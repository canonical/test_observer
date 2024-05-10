import contextlib

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Stage,
    TestExecution,
    TestExecutionRerunRequest,
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
            .joinedload(Artefact.stage)
            .joinedload(Stage.family)
        )
    )


@router.delete("/reruns")
def delete_rerun_requests(request: DeleteReruns, db: Session = Depends(get_db)):
    return db.execute(
        delete(TestExecutionRerunRequest).where(
            TestExecutionRerunRequest.test_execution_id.in_(request.test_execution_ids)
        )
    )


class _TestExecutionNotFound(ValueError):
    ...
