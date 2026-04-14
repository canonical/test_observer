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

from sqlalchemy.orm import Session

from test_observer.common.helpers import get_artefact_url
from test_observer.data_access.models import (
    Artefact,
    Notification,
    User,
)
from test_observer.data_access.models_enums import NotificationType
from test_observer.external_apis.issue_creator import IssueCreator, JiraIssueContext
from test_observer.external_apis.jira import get_jira_client
from test_observer.external_apis.jira.jira_client import JiraClient

logger = logging.getLogger(__name__)


@dataclass
class BatchReviewerAssignedMessage:
    """Context of a batch of reviewers being assigned to an artefact

    Used for notifications and issue creation"""

    artefact: Artefact
    assigned_reviews: list[tuple[User, list[NotificationType]]]


def batch_create_review_notifications(
    db: Session,
    reviewers: list[User],
    artefact: Artefact,
    notification_type: NotificationType,
) -> None:
    """Create notifications for a batch of newly assigned reviewers.

    Args:
        db: Database session
        reviewers: List of users who were newly assigned as reviewers
        artefact: The artefact they were assigned to review
        notification_type: The type of notification to create
    """
    notifications = []
    for reviewer in reviewers:
        notification = Notification(
            user_id=reviewer.id, notification_type=notification_type, target_url=get_artefact_url(artefact)
        )
        notifications.append(notification)
    db.add_all(notifications)


def batch_create_jira_reviewer_cards(
    new_reviewers: BatchReviewerAssignedMessage,
    jira_client: JiraClient | None = None,
) -> None:
    """Attempt to create Jira review cards for a batch of reviewers.

    Args:
        new_reviewers: Context of the batch of reviewers being assigned new reviews
        jira_client: Optional Jira client. If not provided, will attempt to get one.
    """
    if new_reviewers.artefact.jira_issue is None:
        raise ValueError(
            f"Artefact {new_reviewers.artefact.id} does not have a Jira issue. Cannot create review cards."
        )
    if not jira_client:
        try:
            jira_client = get_jira_client()
        except Exception:
            logger.exception("Failed to get Jira client; skipping Jira card creation")
            return

    issue_creator = IssueCreator(
        jira_ctx=JiraIssueContext(
            client=jira_client,
            parent_issue=new_reviewers.artefact.jira_issue,
        )
    )

    for reviewer, notification_types in new_reviewers.assigned_reviews:
        try:
            for notification_type in notification_types:
                issue_creator.create_review_issue(new_reviewers.artefact, reviewer, notification_type)
        except Exception:
            logger.exception(
                f"Failed to create Jira review cards for reviewer {reviewer.id} on artefact {new_reviewers.artefact.id}"
            )
