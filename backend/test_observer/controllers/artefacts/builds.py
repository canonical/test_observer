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
