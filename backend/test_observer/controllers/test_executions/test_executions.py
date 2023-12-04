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


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    Stage,
    TestExecution,
)
from test_observer.data_access.models_enums import TestExecutionStatus
from test_observer.data_access.repository import get_or_create
from test_observer.data_access.setup import get_db

from .models import StartTestExecutionRequest, TestExecutionsPatchRequest

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
                "track": request.track,
                "store": request.store,
                "series": request.series,
                "repo": request.repo,
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
        return {"id": test_execution.id}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{id}")
def patch_test_execution(
    id: int,
    request: TestExecutionsPatchRequest,
    db: Session = Depends(get_db),
):
    test_execution = db.get(TestExecution, id)

    if test_execution is None:
        raise HTTPException(status_code=404, detail="TestExecution not found")

    if request.c3_link is not None:
        test_execution.c3_link = str(request.c3_link)

    if request.ci_link is not None:
        test_execution.ci_link = str(request.ci_link)

    if request.status is not None:
        test_execution.status = request.status

    if request.review_status is not None:
        test_execution.review_status = request.review_status

    if request.review_comment is not None:
        test_execution.review_comment = request.review_comment

    db.commit()
