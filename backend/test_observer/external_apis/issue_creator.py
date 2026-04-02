# Copyright 2026 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import logging

from pydantic import BaseModel

from test_observer.common.helpers import get_artefact_url
from test_observer.data_access.models import Artefact, User
from test_observer.external_apis.jira import JiraClient

logger = logging.getLogger(__name__)


class JiraIssueContext(BaseModel):
    """Holds information needed to create Jira issues"""

    client: JiraClient
    parent_issue: str

    model_config = {"arbitrary_types_allowed": True}

    @property
    def project_key(self) -> str:
        """Extract Jira project key from parent issue key"""
        return self.parent_issue.split("-")[0]


class IssueCreator:
    """Creates issues across multiple issue tracking systems (Jira, GitHub, etc.)"""

    def __init__(
        self,
        jira_ctx: JiraIssueContext | None = None,
    ):
        """Initialize IssueCreator with optional contexts

        Args:
            jira_ctx: context for creating Jira issues
        """
        self.jira_ctx = jira_ctx

    def create_issue(
        self,
        summary: str,
        description: str,
        issue_type: str = "Task",
    ) -> None:
        """Create one issue in all configured clients

        Args:
            summary: Issue title/summary
            description: Issue description
            issue_type: Issue type (default: "Task")

        Raises:
            ValueError: If no context is configured
        """
        if not self.jira_ctx:
            raise ValueError("No issue creation context configured")

        logger.info(f"Creating Jira issue: {summary}")
        self.jira_ctx.client.create_issue(
            project_key=self.jira_ctx.project_key,
            summary=summary,
            issue_type=issue_type,
            description=description,
            parent_issue_key=self.jira_ctx.parent_issue,
        )

    def create_review_issues(
        self,
        artefact: Artefact,
        reviewer: User,
    ) -> None:
        """Create two review issues for an artefact and reviewer

        Creates:
        1. Artefact review issue: "Review artefact {name} version {version} - {reviewer}"
        2. Environment review issue: "Review environments of Artefact {name} version {version} - {reviewer}"

        Args:
            artefact: The artefact to create review issues for
            reviewer: The user to assign the review issues to

        Raises:
            ValueError: If artefact has no reviewers or reviewer is not in reviewers list
        """
        if not artefact.reviewers:
            raise ValueError(
                f"Artefact {artefact.id} has no reviewers assigned. Cannot create review cards without reviewers."
            )

        if reviewer not in artefact.reviewers:
            raise ValueError(
                f"Artefact {artefact.id} reviewers do not include user {reviewer.id}. "
                "Cannot create review cards for non-reviewer."
            )

        artefact_summary = f"Review artefact {artefact.name} version {artefact.version} - {reviewer.name}"
        artefact_url = get_artefact_url(artefact)
        artefact_description = (
            f"Review artefact {artefact.name} version {artefact.version}\n\nArtefact page: {artefact_url}"
        )

        self.create_issue(
            summary=artefact_summary,
            description=artefact_description,
            issue_type="Task",
        )

        environment_summary = (
            f"Review environments of Artefact {artefact.name} version {artefact.version} - {reviewer.name}"
        )
        environment_description = (
            f"Review test environments for artefact {artefact.name} version {artefact.version}\n\n"
            f"Artefact page: {artefact_url}"
        )

        self.create_issue(
            summary=environment_summary,
            description=environment_description,
            issue_type="Task",
        )
