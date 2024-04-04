import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    Stage,
    TestExecution,
    User,
)
from test_observer.data_access.models_enums import TestExecutionStatus
from test_observer.data_access.repository import get_or_create
from test_observer.data_access.setup import get_db

from .logic import reset_test_execution
from .models import StartTestExecutionRequest

router = APIRouter()


@router.put("/start-test")
def start_test_execution(
    request: StartTestExecutionRequest, db: Session = Depends(get_db)
):
    stage = (
        db.query(Stage)
        .filter(
            Stage.name == request.execution_stage,
            Stage.family.has(name=request.family),
        )
        .one()
    )

    try:
        artefact = get_or_create(
            db,
            Artefact,
            filter_kwargs={
                "name": request.name,
                "version": request.version,
                "track": request.track if request.track is not None else "",
                "store": request.store if request.store is not None else "",
                "series": request.series if request.series is not None else "",
                "repo": request.repo if request.repo is not None else "",
            },
            creation_kwargs={"stage_id": stage.id},
        )

        environment = get_or_create(
            db,
            Environment,
            filter_kwargs={"name": request.environment, "architecture": request.arch},
        )

        artefact_build = get_or_create(
            db,
            ArtefactBuild,
            filter_kwargs={
                "architecture": request.arch,
                "revision": request.revision,
                "artefact_id": artefact.id,
            },
        )

        test_execution = get_or_create(
            db,
            TestExecution,
            filter_kwargs={
                "environment_id": environment.id,
                "artefact_build_id": artefact_build.id,
            },
            creation_kwargs={
                "status": TestExecutionStatus.IN_PROGRESS,
                "ci_link": request.ci_link,
            },
        )

        if test_execution.ci_link != request.ci_link:
            reset_test_execution(request, db, test_execution)

        if artefact.assignee_id is None and (users := db.query(User).all()):
            artefact.assignee = random.choice(users)
            db.commit()

        return {"id": test_execution.id}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
