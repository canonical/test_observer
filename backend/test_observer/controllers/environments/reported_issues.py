# Copyright (C) 2023 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.data_access.models import EnvironmentIssue
from test_observer.data_access.setup import get_db

from .models import EnvironmentReportedIssueRequest, EnvironmentReportedIssueResponse

router = APIRouter()

endpoint = "/reported-issues"


@router.get(endpoint, response_model=list[EnvironmentReportedIssueResponse])
def get_reported_issues(
    is_confirmed: bool | None = None, db: Session = Depends(get_db)
):
    stmt = select(EnvironmentIssue)
    if is_confirmed is not None:
        stmt = stmt.where(EnvironmentIssue.is_confirmed == is_confirmed)
    return db.execute(stmt).scalars()


@router.post(endpoint, response_model=EnvironmentReportedIssueResponse)
def create_reported_issue(
    request: EnvironmentReportedIssueRequest, db: Session = Depends(get_db)
):
    issue = EnvironmentIssue(
        environment_name=request.environment_name,
        url=request.url,
        description=request.description,
        is_confirmed=request.is_confirmed,
    )
    db.add(issue)
    db.commit()

    return issue


@router.put(endpoint + "/{issue_id}", response_model=EnvironmentReportedIssueResponse)
def update_reported_issue(
    issue_id: int,
    request: EnvironmentReportedIssueRequest,
    db: Session = Depends(get_db),
):
    issue = db.get(EnvironmentIssue, issue_id)
    for field in request.model_fields:
        setattr(issue, field, getattr(request, field))
    db.commit()
    return issue


@router.delete(endpoint + "/{issue_id}")
def delete_reported_issue(issue_id: int, db: Session = Depends(get_db)):
    db.delete(db.get(EnvironmentIssue, issue_id))
    db.commit()
