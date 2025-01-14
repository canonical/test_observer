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

from fastapi import APIRouter, Body, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

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
    StartImageTestExecutionRequest,
    StartSnapTestExecutionRequest,
)

router = APIRouter()


class StartTestExecutionController:
    def __init__(
        self,
        request: StartSnapTestExecutionRequest
        | StartDebTestExecutionRequest
        | StartCharmTestExecutionRequest
        | StartImageTestExecutionRequest = Body(discriminator="family"),
        db: Session = Depends(get_db),
    ):
        self.request = request
        self.db = db

    def execute(self):
        self.create_artefact()
        self.create_environment()
        self.create_artefact_build()
        self.create_artefact_build_environment()
        self.create_test_execution()

        self.delete_related_rerun_requests()

        self.assign_reviewer()

        return {"id": self.test_execution.id}

    def assign_reviewer(self):
        if self.artefact.assignee_id is None and (users := self.db.query(User).all()):
            self.artefact.assignee = random.choice(users)
            self.db.commit()

    def create_test_execution(self):
        self.test_execution = get_or_create(
            self.db,
            TestExecution,
            filter_kwargs={
                "ci_link": self.request.ci_link,
            },
            creation_kwargs={
                "status": self.request.initial_status,
                "environment_id": self.environment.id,
                "artefact_build_id": self.artefact_build.id,
                "test_plan": self.request.test_plan,
            },
        )

    def create_artefact_build_environment(self):
        get_or_create(
            self.db,
            ArtefactBuildEnvironmentReview,
            filter_kwargs={
                "environment_id": self.environment.id,
                "artefact_build_id": self.artefact_build.id,
            },
        )

    def create_artefact_build(self):
        self.artefact_build = get_or_create(
            self.db,
            ArtefactBuild,
            filter_kwargs={
                "architecture": self.request.arch,
                "revision": getattr(self.request, "revision", None),
                "artefact_id": self.artefact.id,
            },
        )

    def create_environment(self):
        self.environment = get_or_create(
            self.db,
            Environment,
            filter_kwargs={
                "name": self.request.environment,
                "architecture": self.request.arch,
            },
        )

    def create_artefact(self) -> None:
        self.artefact = get_or_create(
            self.db,
            Artefact,
            filter_kwargs={
                "name": self.request.name,
                "version": self.request.version,
                "family": self.request.family,
                "store": getattr(self.request, "store", ""),
                "track": getattr(self.request, "track", ""),
                "series": getattr(self.request, "series", ""),
                "repo": getattr(self.request, "repo", ""),
                "os": getattr(self.request, "os", ""),
                "release": getattr(self.request, "release", ""),
                "sha256": getattr(self.request, "sha256", ""),
                "owner": getattr(self.request, "owner", ""),
                "image_url": getattr(self.request, "image_url", ""),
            },
            creation_kwargs={"stage": self.request.execution_stage},
        )

    def delete_related_rerun_requests(self):
        related_test_execution_runs = self.db.scalars(
            select(TestExecution)
            .where(
                TestExecution.artefact_build_id == self.artefact_build.id,
                TestExecution.environment_id == self.environment.id,
                TestExecution.test_plan == self.test_execution.test_plan,
            )
            .options(selectinload(TestExecution.rerun_request))
        )

        for te in related_test_execution_runs:
            rerun_request = te.rerun_request
            if rerun_request:
                self.db.delete(rerun_request)

        self.db.commit()


@router.put("/start-test")
def start_test_execution(
    test_starter: StartTestExecutionController = Depends(StartTestExecutionController),
):
    return test_starter.execute()
