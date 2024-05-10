from fastapi import APIRouter, Depends, HTTPException
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


@router.post("/reruns")
def create_a_rerun_request(request: RerunRequest, db: Session = Depends(get_db)):
    te = db.get(TestExecution, request.test_execution_id)
    if not te:
        msg = f"No test execution with id {request.test_execution_id} found"
        raise HTTPException(status_code=404, detail=msg)

    get_or_create(db, TestExecutionRerunRequest, {"test_execution_id": te.id})


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
