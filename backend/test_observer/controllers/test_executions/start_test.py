# Copyright 2024 Canonical Ltd.
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

import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from test_observer.controllers.test_executions.logic import (
    delete_related_rerun_requests,
)
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    ArtefactBuildEnvironmentReview,
    Environment,
    Stage,
    TestExecution,
    User,
)
from test_observer.data_access.models_enums import TestExecutionStatus
from test_observer.data_access.repository import get_or_create
from test_observer.data_access.setup import get_db

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

        get_or_create(
            db,
            ArtefactBuildEnvironmentReview,
            filter_kwargs={
                "environment_id": environment.id,
                "artefact_build_id": artefact_build.id,
            },
        )

        test_execution = get_or_create(
            db,
            TestExecution,
            filter_kwargs={
                "ci_link": request.ci_link,
            },
            creation_kwargs={
                "status": TestExecutionStatus.IN_PROGRESS,
                "environment_id": environment.id,
                "artefact_build_id": artefact_build.id,
                "test_plan": request.test_plan,
            },
        )

        delete_related_rerun_requests(
            db,
            test_execution.artefact_build_id,
            test_execution.environment_id,
            test_execution.test_plan,
        )

        if artefact.assignee_id is None and (users := db.query(User).all()):
            artefact.assignee = random.choice(users)
            db.commit()

        return {"id": test_execution.id}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
