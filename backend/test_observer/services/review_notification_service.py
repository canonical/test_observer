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


def notify_reviewer_assigned(
    db: Session,
    reviewer: User,
    artefact: Artefact,
    notification_type: NotificationType,
    jira_client: JiraClient | None = None,
) -> None:
    """Create a notification and Jira card for a newly assigned reviewer.

    Args:
        db: Database session
        reviewer: The user who was assigned as a reviewer
        artefact: The artefact they were assigned to review
        notification_type: The type of notification to create
        jira_client: Optional Jira client.
    """
    target_url = get_artefact_url(artefact)

    with db.begin_nested():
        notification = Notification(
            user_id=reviewer.id,
            notification_type=notification_type,
            target_url=target_url,
        )
        db.add(notification)
        db.flush()

    logger.info(f"Created {notification_type} notification for user {reviewer.id} on artefact {artefact.id}")

    _create_jira_review_cards(artefact, reviewer, jira_client)


def _create_jira_review_cards(
    artefact: Artefact,
    reviewer: User,
    jira_client: JiraClient | None = None,
) -> None:
    """Attempt to create Jira review cards for a reviewer.

    Args:
        artefact: The artefact to create review cards for
        reviewer: The user to assign the review cards to
        jira_client: Optional Jira client. If not provided, will attempt to get one.
    """
    if not artefact.jira_issue:
        logger.info(f"Artefact {artefact.id} has no jira_issue; skipping Jira card creation")
        return

    if jira_client is None:
        try:
            jira_client = get_jira_client()
        except ValueError:
            logger.info("Jira is not configured; skipping card creation")
            return

    try:
        issue_creator = IssueCreator(
            jira_ctx=JiraIssueContext(
                client=jira_client,
                parent_issue=artefact.jira_issue,
            )
        )
        issue_creator.create_review_issues(artefact, reviewer)
        logger.info(f"Created Jira review cards for reviewer {reviewer.id} on artefact {artefact.id}")
    except Exception:
        logger.exception(
            f"Failed to create Jira review cards for reviewer {reviewer.id} "
            f"on artefact {artefact.id}"
        )


def batch_notify_reviewers_assigned(
    db: Session,
    reviewers: list[User],
    artefact: Artefact,
    notification_type: NotificationType,
) -> None:
    """Create notifications for a batch of newly assigned reviewers.

    Iterates through reviewers and creates notifications/Jira cards for each.
    Errors are logged but don't block processing of remaining reviewers.

    Args:
        db: Database session
        reviewers: List of users who were newly assigned as reviewers
        artefact: The artefact they were assigned to review
        notification_type: The type of notification to create
    """
    if not reviewers:
        logger.info(f"No reviewers to notify for artefact {artefact.id}")
        return

    if not artefact.jira_issue:
        logger.info(f"Artefact {artefact.id} has no jira_issue; skipping Jira card creation for all reviewers")
        return

    jira_client = get_jira_client()
    for reviewer in reviewers:
        try:
            notify_reviewer_assigned(db, reviewer, artefact, notification_type, jira_client)
        except Exception:
            logger.exception(
                f"Failed to create {notification_type} notification for reviewer {reviewer.id} "
                f"on artefact {artefact.id}"
            )
