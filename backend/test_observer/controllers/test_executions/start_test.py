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

from fastapi import Body, Depends, Security
from sqlalchemy import select
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
from test_observer.data_access.queries import match_artefact
from test_observer.data_access.repository import (
    create_test_execution_relevant_link,
    get_or_create,
)
from test_observer.data_access.setup import get_db
from test_observer.external_apis.issue_creator import IssueCreator, JiraIssueContext
from test_observer.external_apis.jira.jira_client import JiraClient

from .models import (
    StartCharmTestExecutionRequest,
    StartDebTestExecutionRequest,
    StartImageTestExecutionRequest,
    StartSnapTestExecutionRequest,
)
from .router import router

logger = logging.getLogger(__name__)

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
        env_reviews = [env_review for build in self.artefact.latest_builds for env_review in build.environment_reviews]

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
        if self.request.needs_assignment is False or len(self.artefact.reviewers) > 0:
            return

        rule_ids = self.db.execute(match_artefact(self.artefact)).scalars().all()
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
                self.artefact.reviewers += random.sample(users, min(len(users), number_of_reviewers_to_assign))
                self._assign_reviewers_to_environments()
                self.artefact.due_date = self.determine_due_date()

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


def create_artefact_review_cards(
    artefact: Artefact,
    reviewer: User,
    jira_client: JiraClient,
) -> None:
    """Create Jira review cards for an artefact and a reviewer

    The cards are titled:
        - "Review artefact {artefact.name} version {artefact.version} - {reviewer.name}"
        - "Review environments of Artefact {artefact.name} version {artefact.version} - {reviewer.name}"
    They are linked to the artefact's Jira issue (`artefact.jira_issue`)

    Args:
        artefact: The artefact to create review cards for
        reviewer: The user to assign the review card to

    Raises:
        ValueError: If artefact has no jira_issue, no reviewers, or reviewer not in reviewers list
        Exception: If card creation fails
    """
    if not artefact.jira_issue:
        raise ValueError(
            f"Artefact {artefact.id} has no linked Jira issue (artefact.jira_issue is None). "
            "Cannot create review cards without a parent issue."
        )

    if not artefact.reviewers:
        raise ValueError(
            f"Artefact {artefact.id} has no reviewers assigned. Cannot create review cards without reviewers."
        )

    if reviewer not in artefact.reviewers:
        raise ValueError(
            f"Artefact {artefact.id} reviewers do not include user {reviewer.id}. "
            "Cannot create review cards for non-reviewer."
        )

    try:
        issue_creator = IssueCreator(
            JiraIssueContext(
                client=jira_client,
                parent_issue=artefact.jira_issue,
            )
        )
        issue_creator.create_review_issues(artefact, reviewer)

    except Exception as e:
        logger.error(f"Failed to create Jira review cards for artefact {artefact.id} and user {reviewer.id}: {e}")
        raise
