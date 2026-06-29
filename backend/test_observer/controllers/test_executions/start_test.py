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

import logging
import random
from datetime import date, timedelta

from fastapi import Body, Depends, HTTPException, Security
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.common.enums import Permission
from test_observer.common.permissions import permission_checker
from test_observer.common.review_notification import (
    BatchReviewerAssignedMessage,
    batch_create_jira_reviewer_cards,
    batch_create_review_notifications,
)
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
    calculate_bundled_builds_hash,
)
from test_observer.data_access.models_enums import NotificationType
from test_observer.data_access.queries import match_artefact_considering_specificity
from test_observer.data_access.repository import (
    create_test_execution_relevant_link,
    get_or_create,
)
from test_observer.data_access.setup import get_db
from test_observer.external_apis.jira import get_jira_client
from test_observer.external_apis.jira.jira_client import JiraClient

from .models import (
    StartCharmTestExecutionRequest,
    StartDebTestExecutionRequest,
    StartImageTestExecutionRequest,
    StartSnapTestExecutionRequest,
    StartSolutionTestExecutionRequest,
)
from .router import router

logger = logging.getLogger(__name__)

ENVIRONMENTS_PER_REVIEWER = 50


def require_jira_client() -> JiraClient:
    """FastAPI dependency that returns a configured JiraClient.

    Raises:
        HTTPException: 500 if Jira credentials are not fully configured.
    """
    try:
        return get_jira_client()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


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
            | StartSolutionTestExecutionRequest
        ) = Body(discriminator="family"),
        db: Session = Depends(get_db),
    ):
        self.request = request
        self.db = db

    def execute(self):
        self.create_artefact()
        # arch must be resolved after the artefact exists: for an existing image the
        # request may omit arch, in which case it is derived from the image's build.
        self.resolved_arch = self._resolve_arch()
        self.create_environment()
        self.create_artefact_build()
        self.create_artefact_build_environment()
        self.create_test_plan()
        self.create_test_execution()
        self.create_relevant_links()
        self.delete_rerun_request()

        new_reviewers = self.assign_reviewer()

        self.db.commit()

        # create jira cards for new reviewers after db commit
        if new_reviewers is not None:
            batch_create_jira_reviewer_cards(new_reviewers)

        return {"id": self.test_execution.id}

    def _assign_reviewers_to_environments(self) -> list[User]:
        """Assigns reviewers to environment reviews

        Tries to balance the number of environment reviews assigned to each reviewer.
        Returns the list of reviewers that were newly assigned to at least one environment review.
        """
        env_reviews = [env_review for build in self.artefact.latest_builds for env_review in build.environment_reviews]

        # sort reviewers based on how many environments are assigned to them, then assign the same quantity to every one
        reviewers_to_assignment_count = {reviewer.id: 0 for reviewer in self.artefact.reviewers}
        for env_review in env_reviews:
            for reviewer in env_review.reviewers:
                if reviewer.id in reviewers_to_assignment_count:
                    reviewers_to_assignment_count[reviewer.id] += 1

        # reviewers sorted by how many environment reviews they are already assigned to, ascending
        reviewers_sorted = sorted(
            self.artefact.reviewers,
            key=lambda r: reviewers_to_assignment_count[r.id],
        )

        reviews_per_reviewer = _ceil_division(len(env_reviews), len(self.artefact.reviewers))

        # we pick the reviewer with the least amount of assignments
        # and assign to them as many environments as possible
        # until they reach the reviews_per_reviewer limit,
        # then we move on to the next reviewer in the sorted list and
        # repeat until all environment reviews have a reviewer assigned.
        # since reviews_per_reviewer is ceil(len(env_reviews) / len(reviewers)),
        # we are guaranteed to have enough reviewers to assign to all environment reviews
        reviewers_sorted_idx = 0
        newly_assigned_environment_reviewers: set[User] = set()
        for env_review in env_reviews:
            if env_review.reviewers and env_review.reviewers[0] in self.artefact.reviewers:
                continue
            if reviewers_to_assignment_count[reviewers_sorted[reviewers_sorted_idx].id] >= reviews_per_reviewer:
                reviewers_sorted_idx += 1
            reviewer = reviewers_sorted[reviewers_sorted_idx]
            env_review.reviewers = [reviewer]
            newly_assigned_environment_reviewers.add(reviewer)
            reviewers_to_assignment_count[reviewer.id] += 1

        with self.db.begin_nested():
            batch_create_review_notifications(
                self.db,
                list(newly_assigned_environment_reviewers),
                self.artefact,
                NotificationType.USER_ASSIGNED_ENVIRONMENT_REVIEW,
            )

        return list(newly_assigned_environment_reviewers)

    def assign_reviewer(self) -> BatchReviewerAssignedMessage | None:
        if self.request.needs_assignment is False or len(self.artefact.reviewers) > 0:
            return None

        rule_ids = self.db.execute(match_artefact_considering_specificity(self.artefact)).scalars().all()
        if len(rule_ids) > 0:
            users = (
                self.db.execute(
                    select(User)
                    .join(User.teams)
                    .join(Team.artefact_matching_rules)
                    .where(ArtefactMatchingRule.id.in_(rule_ids))
                    .where(User.id.not_in([r.id for r in self.artefact.reviewers]))
                    .distinct()
                )
                .scalars()
                .all()
            )

            if users:
                environment_count = sum(len(b.test_executions) for b in self.artefact.builds)
                expected_number_of_reviewers = _ceil_division(environment_count, ENVIRONMENTS_PER_REVIEWER)
                number_of_reviewers_to_assign = max(0, expected_number_of_reviewers - len(self.artefact.reviewers))
                newly_assigned_reviewers = random.sample(users, min(len(users), number_of_reviewers_to_assign))
                self.artefact.reviewers += newly_assigned_reviewers
                newly_assigned_environment_reviewers = self._assign_reviewers_to_environments()
                self.artefact.due_date = self.determine_due_date()

                with self.db.begin_nested():
                    batch_create_review_notifications(
                        self.db,
                        newly_assigned_reviewers,
                        self.artefact,
                        NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW,
                    )

                if self.artefact.jira_issue is not None:
                    artefact_reviews = [
                        (reviewer, [NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW])
                        for reviewer in newly_assigned_reviewers
                    ]
                    environment_reviews = [
                        (reviewer, [NotificationType.USER_ASSIGNED_ENVIRONMENT_REVIEW])
                        for reviewer in newly_assigned_environment_reviewers
                    ]
                    return BatchReviewerAssignedMessage(
                        artefact=self.artefact,
                        assigned_reviews=artefact_reviews + environment_reviews,
                    )

        return None

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
                "architecture": self.resolved_arch,
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
                "architecture": self.resolved_arch,
            },
        )

    def create_artefact(self) -> None:
        # The lookup filter must hold exactly the artefact's family-specific unique key;
        # any other fields go in creation_kwargs so a differing value can't miss the
        # existing row and then trip the unique constraint on insert.
        filter_kwargs = {
            "name": self.request.name,
            "version": self.request.version,
            "family": self.request.family,
        }
        creation_kwargs: dict = {"stage": self.request.execution_stage}

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

            # An image is identified by its sha256 alone, so an existing image can be
            # tested by submitting only its sha256; the rest is needed only to create it.
            case StartImageTestExecutionRequest():
                filter_kwargs = {"family": self.request.family, "sha256": self.request.sha256}
                if self.db.query(Artefact).filter_by(**filter_kwargs).one_or_none() is None and any(
                    getattr(self.request, field) is None for field in self.request.REQUIRED_CREATION_FIELDS
                ):
                    raise HTTPException(
                        status_code=422,
                        detail="No image with this sha256 exists yet; provide the full image details to create it.",
                    )
                creation_kwargs |= {
                    "name": self.request.name,
                    "version": self.request.version,
                    "os": self.request.os,
                    "release": self.request.release,
                    "owner": self.request.owner,
                    "image_url": str(self.request.image_url),
                }

            # In other families, a single artefact will progress through stages,
            # i.e. move from edge to stable. Solutions are different. Different stages are treated
            # as different artefacts for solutions.
            case StartSolutionTestExecutionRequest():
                filter_kwargs["track"] = self.request.track
                filter_kwargs["source"] = self.request.source
                filter_kwargs["stage"] = self.request.execution_stage
                filter_kwargs["bundled_builds_hash"] = calculate_bundled_builds_hash([])
                creation_kwargs = {}

        self.artefact = get_or_create(self.db, Artefact, filter_kwargs=filter_kwargs, creation_kwargs=creation_kwargs)

    def _resolve_arch(self) -> str:
        if self.request.arch is not None:
            return self.request.arch

        # arch was omitted: only valid for an existing image, derive it from its build.
        architectures = self.artefact.architectures
        if len(architectures) == 1:
            return next(iter(architectures))

        raise HTTPException(
            status_code=422,
            detail="'arch' is required and could not be derived from the image's builds.",
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
