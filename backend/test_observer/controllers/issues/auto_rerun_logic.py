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

from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.data_access.models import (
    IssueTestResultAttachmentRule,
    IssueTestResultAttachment,
)
from test_observer.controllers.test_executions.reruns import modify_reruns
from test_observer.controllers.test_executions.models import RerunRequest


def trigger_reruns_for_test_execution_ids(
    db: Session,
    test_execution_ids: set[int],
) -> None:
    if not test_execution_ids:
        return

    modify_reruns(
        db,
        RerunRequest(
            test_execution_ids=test_execution_ids,
        ),
    )


def trigger_reruns_for_attachment_rule(
    db: Session,
    attachment_rule: IssueTestResultAttachmentRule,
) -> None:
    """
    Trigger reruns for all test executions attached to an attachment rule.
    This is called when auto_rerun_on_attach is enabled on a rule.
    """
    # Get all test result attachments for this rule
    attachments = (
        db.execute(
            select(IssueTestResultAttachment).where(
                IssueTestResultAttachment.attachment_rule_id == attachment_rule.id
            )
        )
        .scalars()
        .all()
    )

    test_execution_ids = {
        attachment.test_result.test_execution_id
        for attachment in attachments
        if attachment.test_result is not None
    }

    trigger_reruns_for_test_execution_ids(db, test_execution_ids)
