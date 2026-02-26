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

from fastapi import APIRouter, Depends, Security
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.common.permissions import Permission, permission_checker
from test_observer.data_access.models import TestCaseIssue
from test_observer.data_access.setup import get_db

from .models import TestReportedIssueRequest, TestReportedIssueResponse

router = APIRouter()


endpoint = "/reported-issues"


@router.get(
    endpoint,
    response_model=list[TestReportedIssueResponse],
    dependencies=[
        Security(permission_checker, scopes=[Permission.view_test_case_reported_issue])
    ],
)
def get_reported_issues(
    template_id: str | None = None,
    case_name: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(TestCaseIssue)
    if template_id:
        stmt = stmt.where(TestCaseIssue.template_id == template_id)
    if case_name:
        stmt = stmt.where(TestCaseIssue.case_name == case_name)
    return db.execute(stmt).scalars()


@router.post(
    endpoint,
    response_model=TestReportedIssueResponse,
    dependencies=[
        Security(
            permission_checker, scopes=[Permission.change_test_case_reported_issue]
        )
    ],
)
def create_reported_issue(
    request: TestReportedIssueRequest, db: Session = Depends(get_db)
):
    issue = TestCaseIssue(
        template_id=request.template_id,
        url=request.url,
        description=request.description,
        case_name=request.case_name,
    )
    db.add(issue)
    db.commit()

    return issue


@router.put(
    endpoint + "/{issue_id}",
    response_model=TestReportedIssueResponse,
    dependencies=[
        Security(
            permission_checker, scopes=[Permission.change_test_case_reported_issue]
        )
    ],
)
def update_reported_issue(
    issue_id: int, request: TestReportedIssueRequest, db: Session = Depends(get_db)
):
    issue = db.get(TestCaseIssue, issue_id)
    for field in request.model_fields:
        setattr(issue, field, getattr(request, field))
    db.commit()
    return issue


@router.delete(
    endpoint + "/{issue_id}",
    dependencies=[
        Security(
            permission_checker, scopes=[Permission.change_test_case_reported_issue]
        )
    ],
)
def delete_reported_issue(issue_id: int, db: Session = Depends(get_db)):
    db.delete(db.get(TestCaseIssue, issue_id))
    db.commit()
