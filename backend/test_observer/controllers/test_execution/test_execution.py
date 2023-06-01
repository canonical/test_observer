from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    Stage,
    TestExecution,
)
from src.data_access.models_enums import TestExecutionStatus
from src.data_access.setup import get_db

from .models import StartTestExecutionRequest

router = APIRouter()


@router.put("/start")
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

    artefact = Artefact(
        name=request.name,
        version=request.version,
        source=request.source,
        stage=stage,
    )

    environment = Environment(name=request.environment, architecture=request.arch)

    artefact_build = ArtefactBuild(
        architecture=request.arch, revision=request.revision, artefact=artefact
    )

    test_execution = TestExecution(
        environment=environment,
        artefact_build=artefact_build,
        status=TestExecutionStatus.IN_PROGRESS,
    )

    db.add(artefact)
    db.add(environment)
    db.add(artefact_build)
    db.add(test_execution)
    db.commit()


@router.patch("/")
def patch_test_execution():
    pass
