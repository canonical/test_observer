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


from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session

from test_observer.common.permissions import Permission, permission_checker
from test_observer.data_access.setup import get_db
from test_observer.data_access.models import (
    IssueTestResultAttachmentRule,
    Issue,
    IssueTestResultAttachmentRuleExecutionMetadata,
)

from .models import (
    IssueTestResultAttachmentRulePostRequest,
    IssueTestResultAttachmentRulePatchRequest,
)

from .shared_models import MinimalIssueTestResultAttachmentRuleResponse

router = APIRouter()


@router.post(
    "/{issue_id}/attachment-rules",
    response_model=MinimalIssueTestResultAttachmentRuleResponse,
    dependencies=[
        Security(permission_checker, scopes=[Permission.change_attachment_rule])
    ],
)
def post_attachment_rule(
    issue_id: int,
    request: IssueTestResultAttachmentRulePostRequest,
    db: Session = Depends(get_db),
):
    # Get the issue
    issue = db.get(Issue, issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Create the attachment rule
    attachment_rule = IssueTestResultAttachmentRule(
        issue_id=issue.id,
        enabled=request.enabled,
        families=request.families,
        environment_names=request.environment_names,
        test_case_names=request.test_case_names,
        template_ids=request.template_ids,
        execution_metadata=[
            IssueTestResultAttachmentRuleExecutionMetadata(
                category=metadata.category,
                value=metadata.value,
            )
            for metadata in request.execution_metadata.to_rows()
        ],
    )

    # Add the attachment rule
    db.add(attachment_rule)
    db.commit()
    db.refresh(attachment_rule)
    return attachment_rule


@router.patch(
    "/{issue_id}/attachment-rules/{attachment_rule_id}",
    response_model=MinimalIssueTestResultAttachmentRuleResponse,
    dependencies=[
        Security(permission_checker, scopes=[Permission.change_attachment_rule])
    ],
)
def patch_attachment_rule(
    issue_id: int,
    attachment_rule_id: int,
    request: IssueTestResultAttachmentRulePatchRequest,
    db: Session = Depends(get_db),
):
    # Get the attachment rule
    attachment_rule = db.get(IssueTestResultAttachmentRule, attachment_rule_id)
    if attachment_rule is None:
        raise HTTPException(status_code=404, detail="Attachment rule not found")
    if attachment_rule.issue_id != issue_id:
        raise HTTPException(
            status_code=400, detail="Attachment rule not attached to given issue"
        )

    # Modify the attachment rule
    if request.enabled is not None:
        attachment_rule.enabled = request.enabled

    # Save the attachment rule
    db.commit()
    db.refresh(attachment_rule)
    return attachment_rule


@router.delete(
    "/{issue_id}/attachment-rules/{attachment_rule_id}",
    status_code=204,
    dependencies=[
        Security(permission_checker, scopes=[Permission.change_attachment_rule])
    ],
)
def delete_attachment_rule(
    issue_id: int,
    attachment_rule_id: int,
    db: Session = Depends(get_db),
):
    # Get the attachment rule
    attachment_rule = db.get(IssueTestResultAttachmentRule, attachment_rule_id)
    if attachment_rule is None:
        return
    if attachment_rule.issue_id != issue_id:
        raise HTTPException(
            status_code=400, detail="Attachment rule not attached to given issue"
        )

    # Delete the attachment rule
    db.delete(attachment_rule)
    db.commit()
