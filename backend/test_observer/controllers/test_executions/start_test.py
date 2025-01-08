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


class TestExecutionController:
    def __init__(
        self,
        request: StartSnapTestExecutionRequest
        | StartDebTestExecutionRequest
        | StartCharmTestExecutionRequest = Body(discriminator="family"),
        db: Session = Depends(get_db),
    ):
        self.request = request
        self.db = db

    def execute(self):
        try:
            artefact_filter_kwargs: dict[str, str | int] = {
                "name": self.request.name,
                "version": self.request.version,
            }
            match self.request:
                case StartSnapTestExecutionRequest():
                    artefact_filter_kwargs["store"] = self.request.store
                    artefact_filter_kwargs["track"] = self.request.track
                case StartDebTestExecutionRequest():
                    artefact_filter_kwargs["series"] = self.request.series
                    artefact_filter_kwargs["repo"] = self.request.repo
                case StartCharmTestExecutionRequest():
                    artefact_filter_kwargs["track"] = self.request.track

            artefact = get_or_create(
                self.db,
                Artefact,
                filter_kwargs=artefact_filter_kwargs,
                creation_kwargs={
                    "family": self.request.family.value,
                    "stage": self.request.execution_stage,
                },
            )

            environment = get_or_create(
                self.db,
                Environment,
                filter_kwargs={
                    "name": self.request.environment,
                    "architecture": self.request.arch,
                },
            )

            artefact_build = get_or_create(
                self.db,
                ArtefactBuild,
                filter_kwargs={
                    "architecture": self.request.arch,
                    "revision": self.request.revision
                    if isinstance(self.request, StartSnapTestExecutionRequest)
                    else None,
                    "artefact_id": artefact.id,
                },
            )

            get_or_create(
                self.db,
                ArtefactBuildEnvironmentReview,
                filter_kwargs={
                    "environment_id": environment.id,
                    "artefact_build_id": artefact_build.id,
                },
            )

            test_execution = get_or_create(
                self.db,
                TestExecution,
                filter_kwargs={
                    "ci_link": self.request.ci_link,
                },
                creation_kwargs={
                    "status": self.request.initial_status,
                    "environment_id": environment.id,
                    "artefact_build_id": artefact_build.id,
                    "test_plan": self.request.test_plan,
                },
            )

            delete_related_rerun_requests(
                self.db,
                test_execution.artefact_build_id,
                test_execution.environment_id,
                test_execution.test_plan,
            )

            if artefact.assignee_id is None and (users := self.db.query(User).all()):
                artefact.assignee = random.choice(users)
                self.db.commit()

            return {"id": test_execution.id}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/start-test")
def start_test_execution(
    test_starter: TestExecutionController = Depends(TestExecutionController),
):
    return test_starter.execute()
