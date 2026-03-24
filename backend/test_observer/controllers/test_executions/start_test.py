# Copyright 2024 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import random
from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, Security
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from test_observer.common.permissions import Permission, permission_checker
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    ArtefactBuildEnvironmentReview,
    ArtefactMatchingRule,
    Environment,
    Team,
    TestExecution,
    TestPlan,
    User,
)
from test_observer.data_access.repository import (
    create_test_execution_relevant_link,
    get_or_create,
)
from test_observer.data_access.setup import get_db

from .models import (
    StartCharmTestExecutionRequest,
    StartDebTestExecutionRequest,
    StartImageTestExecutionRequest,
    StartSnapTestExecutionRequest,
)

router = APIRouter()

ENVIRONMENTS_PER_REVIEWER = 50


def _ceil_division(numerator: int, denominator: int) -> int:
    return (numerator + denominator - 1) // denominator


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

    def _assign_reviewers_to_environments(self) -> None:
        env_reviews = [env_review for build in self.artefact.builds for env_review in build.environment_reviews]

        # sort reviewers based on how many environments are assigned to them, then assign the same quantity to every one
        reviewers_to_assignment_count = {reviewer.id: 0 for reviewer in self.artefact.reviewers}
        for env_review in env_reviews:
            for reviewer in env_review.reviewers:
                if reviewer.id in reviewers_to_assignment_count:
                    reviewers_to_assignment_count[reviewer.id] += 1

        reviewers_sorted = sorted(
            self.artefact.reviewers,
            key=lambda r: reviewers_to_assignment_count[r.id],
        )

        reviews_per_reviewer = _ceil_division(len(env_reviews), len(self.artefact.reviewers))

        current_reviewer = 0
        for env_review in env_reviews:
            if env_review.reviewers and env_review.reviewers[0] in self.artefact.reviewers:
                continue
            if reviewers_to_assignment_count[reviewers_sorted[current_reviewer].id] >= reviews_per_reviewer:
                current_reviewer += 1
            env_review.reviewers = [reviewers_sorted[current_reviewer]]
            reviewers_to_assignment_count[reviewers_sorted[current_reviewer].id] += 1

        self.db.commit()

    def assign_reviewer(self):
        if not self.request.needs_assignment:
            return
        if self.artefact.reviewers is not None and len(self.artefact.reviewers) > 0:
            self._assign_reviewers_to_environments()
            return

        # Get reviewers whose teams can review this artefact family
        family_str = self.artefact.family.value

        possible_rules = (
            self.db.execute(
                select(ArtefactMatchingRule).where(
                    and_(
                        ArtefactMatchingRule.family == family_str,
                        or_(ArtefactMatchingRule.stage == self.artefact.stage, ArtefactMatchingRule.stage == ""),
                        or_(ArtefactMatchingRule.track == self.artefact.track, ArtefactMatchingRule.track == ""),
                        or_(ArtefactMatchingRule.branch == self.artefact.branch, ArtefactMatchingRule.branch == ""),
                    ),
                )
            )
            .scalars()
            .all()
        )

        # sort rules by number of non-empty fields to prioritize specificity
        rules_with_score = [
            [r, sum(1 for field in [r.stage, r.track, r.branch] if field != "")] for r in possible_rules
        ]
        sorted_rules = sorted(rules_with_score, key=lambda x: x[1], reverse=True)
        highest_score = sorted_rules[0][1] if sorted_rules else 0
        rules = [r[0] for r in sorted_rules if r[1] == highest_score]

        if rules:
            users = (
                self.db.execute(
                    select(User)
                    .join(User.teams)
                    .join(Team.artefact_matching_rules)
                    .where(ArtefactMatchingRule.id.in_([r.id for r in rules]))
                    .distinct()
                )
                .scalars()
                .all()
            )

            if users:
                # Get number of environments for the artefact, which is ceil(count/ENVIRONMENTS_PER_REVIEWER)
                environment_count = sum(len(b.test_executions) for b in self.artefact.builds)
                expected_number_of_reviewers = _ceil_division(environment_count, ENVIRONMENTS_PER_REVIEWER)

                number_of_reviewers_to_assign = max(
                    0, min(expected_number_of_reviewers, len(users)) - len(self.artefact.reviewers)
                )
                self.artefact.reviewers += random.sample(users, number_of_reviewers_to_assign)
                self._assign_reviewers_to_environments()
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
