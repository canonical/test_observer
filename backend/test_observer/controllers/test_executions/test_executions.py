# Copyright 2023 Canonical Ltd.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Written by:
#        Omar Selo <omar.selo@canonical.com>
#        Nadzeya Hutsko <nadzeya.hutsko@canonical.com>


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from test_observer.data_access.models import (
    TestExecution,
    Stage,
    Artefact,
    ArtefactBuild,
    Environment,
)
from test_observer.data_access.models_enums import TestExecutionStatus
from test_observer.data_access.repository import get_or_create
from test_observer.data_access.setup import get_db

from .models import TestExecutionsPatchRequest, StartTestExecutionRequest

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

    artefact = get_or_create(
        db,
        Artefact,
        name=request.name,
        version=request.version,
        source=request.source,
        stage_id=stage.id,
    )

    environment = get_or_create(
        db,
        Environment,
        name=request.environment,
        architecture=request.arch,
    )

    artefact_build = get_or_create(
        db,
        ArtefactBuild,
        architecture=request.arch,
        revision=request.revision,
        artefact_id=artefact.id,
    )

    test_execution = get_or_create(
        db,
        TestExecution,
        environment_id=environment.id,
        artefact_build_id=artefact_build.id,
        status=TestExecutionStatus.IN_PROGRESS,
    )
    return {"id": test_execution.id}


@router.patch("/{id}")
def patch_test_execution(
    id: int,
    request: TestExecutionsPatchRequest,
    db: Session = Depends(get_db),
):
    test_execution = db.query(TestExecution).filter(TestExecution.id == id).one()
    test_execution.c3_link = request.c3_link
    test_execution.jenkins_link = request.jenkins_link
    test_execution.status = request.status
    db.commit()
