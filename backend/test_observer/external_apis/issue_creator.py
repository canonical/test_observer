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
from dataclasses import dataclass

from test_observer.common.helpers import get_artefact_url
from test_observer.data_access.models import Artefact, User
from test_observer.data_access.models_enums import NotificationType
from test_observer.external_apis.jira import JiraClient

logger = logging.getLogger(__name__)


@dataclass
class JiraIssueContext:
    """Holds information needed to create Jira issues"""

    client: JiraClient
    parent_issue: str

    @property
    def project_key(self) -> str:
        """Extract Jira project key from parent issue key"""
        return self.parent_issue.split("-")[0]


class IssueCreator:
    """Creates issues across multiple issue tracking systems (Jira, GitHub, etc.)"""

    def __init__(
        self,
        jira_ctx: JiraIssueContext,
    ):
        """Initialize IssueCreator

        Args:
            jira_ctx: context for creating Jira issues
        """
        self.jira_ctx = jira_ctx

    def create_issue(
        self,
        summary: str,
        description: str,
        issue_type: str = "Task",
        assignee_id: str | None = None,
    ) -> None:
        """Create one issue in all configured clients

        Args:
            summary: Issue title/summary
            description: Issue description
            issue_type: Issue type (default: "Task")
            assignee_id: Jira account ID to assign the issue to

        Raises:
            ValueError: If no context is configured
        """
        logger.info(f"Creating Jira issue: {summary}")
        self.jira_ctx.client.create_issue(
            project_key=self.jira_ctx.project_key,
            summary=summary,
            issue_type=issue_type,
            description=description,
            parent_issue_key=self.jira_ctx.parent_issue,
            assignee_id=assignee_id,
        )

    def create_review_issue(
        self,
        artefact: Artefact,
        reviewer: User,
        notification_type: NotificationType,
    ) -> None:
        """Create review issue for an artefact and reviewer based on notification type

        Args:
            artefact: The artefact to create a review issue for
            reviewer: The user to assign the review issue to
            notification_type: The type of notification that triggered the issue creation
        """
        if not reviewer.launchpad_handle:
            raise ValueError(
                f"Reviewer {reviewer.id} does not have a launchpad handle. Cannot assign Jira issue to reviewer."
            )
        if reviewer.id not in [r.id for r in artefact.reviewers]:
            raise ValueError(
                f"Artefact {artefact.id} reviewers do not include user {reviewer.id}. "
                "Cannot create review cards for non-reviewer."
            )

        artefact_url = get_artefact_url(artefact)
        assignee_id = self.jira_ctx.client.get_account_id_by_username(reviewer.launchpad_handle)

        if not assignee_id:
            raise ValueError(
                f"Cannot assign Jira issue to reviewer {reviewer.id} "
                "because no Jira account ID was found for that user."
            )

        match notification_type:
            case NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW:
                summary = f"Review artefact {artefact.name} version {artefact.version} - {reviewer.name}"
                description = (
                    f"Review artefact {artefact.name} version {artefact.version}\n\nArtefact page: {artefact_url}"
                )
            case NotificationType.USER_ASSIGNED_ENVIRONMENT_REVIEW:
                summary = (
                    f"Review environments of Artefact {artefact.name} version {artefact.version} - {reviewer.name}"
                )
                description = (
                    f"Review test environments for artefact {artefact.name} version {artefact.version}\n\n"
                    f"Artefact page: {artefact_url}"
                )

        self.create_issue(
            summary=summary,
            description=description,
            issue_type="Task",
            assignee_id=assignee_id,
        )
