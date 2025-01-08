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

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from test_observer.controllers.test_executions.logic import (
    delete_related_rerun_requests,
)
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    ArtefactBuildEnvironmentReview,
    Environment,
    TestExecution,
    User,
)
from test_observer.data_access.repository import get_or_create
from test_observer.data_access.setup import get_db

from .models import (
    StartCharmTestExecutionRequest,
    StartDebTestExecutionRequest,
    StartSnapTestExecutionRequest,
)

router = APIRouter()


class TestExecutionStarter:
    def __init__(self):
        pass

    def execute(
        self,
        request: StartSnapTestExecutionRequest
        | StartDebTestExecutionRequest
        | StartCharmTestExecutionRequest,
        db: Session,
    ):
        try:
            artefact_filter_kwargs: dict[str, str | int] = {
                "name": request.name,
                "version": request.version,
            }
            match request:
                case StartSnapTestExecutionRequest():
                    artefact_filter_kwargs["store"] = request.store
                    artefact_filter_kwargs["track"] = request.track
                case StartDebTestExecutionRequest():
                    artefact_filter_kwargs["series"] = request.series
                    artefact_filter_kwargs["repo"] = request.repo
                case StartCharmTestExecutionRequest():
                    artefact_filter_kwargs["track"] = request.track

            artefact = get_or_create(
                db,
                Artefact,
                filter_kwargs=artefact_filter_kwargs,
                creation_kwargs={
                    "family": request.family.value,
                    "stage": request.execution_stage,
                },
            )

            environment = get_or_create(
                db,
                Environment,
                filter_kwargs={
                    "name": request.environment,
                    "architecture": request.arch,
                },
            )

            artefact_build = get_or_create(
                db,
                ArtefactBuild,
                filter_kwargs={
                    "architecture": request.arch,
                    "revision": request.revision
                    if isinstance(request, StartSnapTestExecutionRequest)
                    else None,
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
                    "status": request.initial_status,
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


@router.put("/start-test")
def start_test_execution(
    request: StartSnapTestExecutionRequest
    | StartDebTestExecutionRequest
    | StartCharmTestExecutionRequest = Body(discriminator="family"),
    db: Session = Depends(get_db),
    test_starter: TestExecutionStarter = Depends(TestExecutionStarter),
):
    return test_starter.execute(request, db)
