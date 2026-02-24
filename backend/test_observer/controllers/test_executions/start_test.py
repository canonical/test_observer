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


from datetime import date, timedelta
import random

from fastapi import APIRouter, Body, Depends, Security
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.common.permissions import Permission, permission_checker
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    ArtefactBuildEnvironmentReview,
    Environment,
    Team,
    TestExecution,
    TestPlan,
    User,
)
from test_observer.data_access.repository import (
    get_or_create,
    create_test_execution_relevant_link,
)
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
        request: (
            StartSnapTestExecutionRequest
            | StartDebTestExecutionRequest
            | StartCharmTestExecutionRequest
            | StartImageTestExecutionRequest
        ) = Body(discriminator="family"),
        db: Session = Depends(get_db),
    ):
        self.request = request
        self.db = db

    def execute(self):
        self.create_artefact()
        self.create_environment()
        self.create_artefact_build()
        self.create_artefact_build_environment()
        self.create_test_plan()
        self.create_test_execution()
        self.create_relevant_links()
        self.delete_rerun_request()

        self.assign_reviewer()

        self.db.commit()

        return {"id": self.test_execution.id}

    def assign_reviewer(self):
        if self.request.needs_assignment and len(self.artefact.reviewers) == 0:
            # Get reviewers whose teams can review this artefact family
            family_str = self.artefact.family.value

            users = (
                self.db.execute(
                    select(User)
                    .join(User.teams)
                    .where(Team.reviewer_families.any(family_str))
                    .distinct()
                )
                .scalars()
                .all()
            )

            if users:
                self.artefact.assignee = random.choice(users)
                self.artefact.due_date = self.determine_due_date()
                self.db.commit()

    def create_test_plan(self):
        self.test_plan = get_or_create(
            self.db,
            TestPlan,
            filter_kwargs={
                "name": self.request.test_plan,
            },
        )

    def create_test_execution(self):
        # If ci_link is None, we cannot uniquely identify the test execution,
        # so always create a new one instead of using get_or_create
        if self.request.ci_link is None:
            self.test_execution = TestExecution(
                status=self.request.initial_status,
                environment_id=self.environment.id,
                artefact_build_id=self.artefact_build.id,
                test_plan_id=self.test_plan.id,
                ci_link=None,
            )
            self.db.add(self.test_execution)
            self.db.flush()
        else:
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
                    "test_plan_id": self.test_plan.id,
                },
            )

    def create_relevant_links(self):
        if self.request.relevant_links:
            for link in self.request.relevant_links:
                create_test_execution_relevant_link(
                    self.db,
                    self.test_execution.id,
                    link.label,
                    link.url,
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
        filter_kwargs = {
            "name": self.request.name,
            "version": self.request.version,
            "family": self.request.family,
        }

        match self.request:
            case StartSnapTestExecutionRequest():
                filter_kwargs["store"] = self.request.store
                filter_kwargs["track"] = self.request.track
                filter_kwargs["branch"] = self.request.branch
            case StartCharmTestExecutionRequest():
                filter_kwargs["track"] = self.request.track
                filter_kwargs["branch"] = self.request.branch
            case StartDebTestExecutionRequest():
                filter_kwargs["series"] = self.request.series
                filter_kwargs["repo"] = self.request.repo
                filter_kwargs["source"] = self.request.source
            case StartImageTestExecutionRequest():
                filter_kwargs["os"] = self.request.os
                filter_kwargs["release"] = self.request.release
                filter_kwargs["sha256"] = self.request.sha256
                filter_kwargs["owner"] = self.request.owner
                filter_kwargs["image_url"] = str(self.request.image_url)

        self.artefact = get_or_create(
            self.db,
            Artefact,
            filter_kwargs=filter_kwargs,
            creation_kwargs={"stage": self.request.execution_stage},
        )

    def delete_rerun_request(self):
        if self.test_execution.rerun_request:
            self.db.delete(self.test_execution.rerun_request)
            self.db.commit()

    def determine_due_date(self):
        name = self.artefact.name
        is_kernel = name.startswith("linux-") or name.endswith("-kernel")
        if not is_kernel:
            # If not a kernel, return a date 10 days from now
            return date.today() + timedelta(days=10)
        return None


@router.put(
    "/start-test",
    dependencies=[Security(permission_checker, scopes=[Permission.change_test])],
)
def start_test_execution(
    test_starter: StartTestExecutionController = Depends(StartTestExecutionController),
):
    return test_starter.execute()
