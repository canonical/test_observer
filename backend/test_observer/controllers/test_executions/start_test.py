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
from os import environ

from fastapi import Body, Depends, Security
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
from test_observer.external_apis.jira import JiraClient

from .models import (
    StartCharmTestExecutionRequest,
    StartDebTestExecutionRequest,
    StartImageTestExecutionRequest,
    StartSnapTestExecutionRequest,
)
from .router import router

logger = logging.getLogger(__name__)

ENVIRONMENTS_PER_REVIEWER = 50


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

                # Get number of environments for the artefact, which is ceil(count/ENVIRONMENTS_PER_REVIEWER)
                environment_count = sum(len(b.test_executions) for b in self.artefact.builds)
                expected_number_of_reviewers = (
                    environment_count + ENVIRONMENTS_PER_REVIEWER - 1
                ) // ENVIRONMENTS_PER_REVIEWER

                if users:
                    self.artefact.reviewers = random.sample(users, min(expected_number_of_reviewers, len(users)))
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


def create_artefact_review_cards(artefact: Artefact, reviewer: User) -> None:
    """Create Jira review cards for an artefact and a reviewer

    The cards are titled:
        - "Review artefact {artefact.name} version {artefact.version} - {reviewer.name}"
        - "Review environments of Artefact {artefact.name} version {artefact.version} - {reviewer.name}"
    They are linked to the artefact's Jira issue (`artefact.jira_issue`)

    Args:
        artefact: The artefact to create review cards for
        reviewer: The user to assign the review card to

    Raises:
        Exception: If Jira credentials are not configured or card creation fails
    """
    jira_cloud_id = environ.get("JIRA_CLOUD_ID")
    jira_email = environ.get("JIRA_EMAIL")
    jira_api_token = environ.get("JIRA_API_TOKEN")
    jira_project_key = environ.get("JIRA_PROJECT_KEY")

    if not all([jira_cloud_id, jira_email, jira_api_token, jira_project_key]):
        logger.warning(
            "Jira credentials not fully configured. Skipping review card creation. "
            "Requires: JIRA_CLOUD_ID, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY"
        )
        return

    if not artefact.jira_issue:
        logger.warning(f"Artefact {artefact.id} has no linked Jira epic. Skipping review card creation.")
        return

    if not artefact.reviewers:
        logger.info(f"Artefact {artefact.id} has no reviewers assigned. Skipping review card creation.")
        return

    try:
        jira_client = JiraClient(
            cloud_id=str(jira_cloud_id),
            email=str(jira_email),
            api_token=str(jira_api_token),
        )

        artefact_summary = f"Review artefact {artefact.name} version {artefact.version} - {reviewer.name}"
        logger.info(f"Creating Jira card: {artefact_summary}")

        jira_client.create_issue(
            project_key=str(jira_project_key),
            summary=artefact_summary,
            issue_type="Task",
            description=f"Review artefact {artefact.name} version {artefact.version}",
            parent_epic_link=artefact.jira_issue,
        )

        environment_summary = (
            f"Review environments of Artefact {artefact.name} version {artefact.version} - {reviewer.name}"
        )
        logger.info(f"Creating Jira card: {environment_summary}")

        jira_client.create_issue(
            project_key=str(jira_project_key),
            summary=environment_summary,
            issue_type="Task",
            description=f"Review test environments for artefact {artefact.name} version {artefact.version}",
            parent_epic_link=artefact.jira_issue,
        )

        logger.info(f"Successfully created review cards for artefact {artefact.id} and user {reviewer.id}")
    except Exception as e:
        logger.error(f"Failed to create Jira review cards for artefact {artefact.id} and user {reviewer.id}: {e}")
