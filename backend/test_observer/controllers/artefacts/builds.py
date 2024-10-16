from fastapi import APIRouter, Depends
from sqlalchemy.orm import selectinload

from test_observer.controllers.artefacts.artefact_retriever import ArtefactRetriever
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    TestExecution,
)

from .models import (
    ArtefactBuildDTO,
)

router = APIRouter(tags=["artefact-builds"])


@router.get("/{artefact_id}/builds", response_model=list[ArtefactBuildDTO])
def get_artefact_builds(
    artefact: Artefact = Depends(
        ArtefactRetriever(
            selectinload(Artefact.builds)
            .selectinload(ArtefactBuild.test_executions)
            .options(
                selectinload(TestExecution.environment),
                selectinload(TestExecution.rerun_request),
            )
        )
    ),
):
    """Get latest artefact builds of an artefact together with their test executions"""
    for artefact_build in artefact.latest_builds:
        artefact_build.test_executions.sort(
            key=lambda test_execution: test_execution.environment.name
        )

    return artefact.latest_builds
