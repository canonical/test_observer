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


from fastapi import APIRouter, Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert as pg_insert

from test_observer.data_access.setup import get_db
from test_observer.data_access.models import Issue, IssueTestResultAttachment

from .models import (
    IssueResponse,
    IssueAttachmentRequest,
)

router = APIRouter()


def modify_issue_attachments(
    db: Session,
    issue_id: int,
    request: IssueAttachmentRequest,
    detach: bool = False,
) -> Issue:
    # Retrieve the issue
    issue = db.get(Issue, issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Add or remove any requested test result attachments
    test_result_ids = set(request.test_results)
    if test_result_ids:
        if detach:
            db.execute(
                delete(IssueTestResultAttachment).where(
                    IssueTestResultAttachment.issue_id == issue_id,
                    IssueTestResultAttachment.test_result_id.in_(test_result_ids),
                )
            )
        else:
            db.execute(
                pg_insert(IssueTestResultAttachment)
                .values(
                    [
                        {"issue_id": issue_id, "test_result_id": test_result_id}
                        for test_result_id in test_result_ids
                    ]
                )
                .on_conflict_do_nothing()
            )

    # Save and return the issue
    db.commit()
    db.refresh(issue)
    return issue


@router.post("/{issue_id}/attach", response_model=IssueResponse)
def add_issue_attachments(
    issue_id: int,
    request: IssueAttachmentRequest,
    db: Session = Depends(get_db),
):
    return modify_issue_attachments(db, issue_id, request, detach=False)


@router.post("/{issue_id}/detach", response_model=IssueResponse)
def remove_issue_attachments(
    issue_id: int,
    request: IssueAttachmentRequest,
    db: Session = Depends(get_db),
):
    return modify_issue_attachments(db, issue_id, request, detach=True)
