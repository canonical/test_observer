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
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.data_access.models import Issue
from test_observer.data_access.setup import get_db
from test_observer.data_access.models_enums import IssueSource
from test_observer.data_access.repository import get_or_create

from .models import (
    IssuePatchRequest,
    IssuePutRequest,
    IssueResponse,
    IssuesGetResponse,
    MinimalIssueResponse,
)
from .issue_url_parser import issue_source_project_key_from_url

router = APIRouter(tags=["issues"])

@router.get("", response_model=IssuesGetResponse)
def get_issues(
    source: IssueSource | None = None,
    project: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(Issue)
    if source:
        stmt = stmt.where(Issue.source == source)
    if project:
        stmt = stmt.where(Issue.project == project)
    issues = db.execute(stmt).scalars().all()
    return IssuesGetResponse(
        issues=[MinimalIssueResponse.model_validate(issue) for issue in issues]
    )

@router.get("/{issue_id}", response_model=IssueResponse)
def get_issue(
    issue_id: int,
    db: Session = Depends(get_db),
):
    issue = db.get(Issue, issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue

def update_issue(db: Session, issue: Issue, request: IssuePatchRequest):
    if request.title is not None:
        issue.title = request.title
    if request.status is not None:
        issue.status = request.status
    db.commit()
    db.refresh(issue)
    return issue

@router.patch("/{issue_id}", response_model=IssueResponse)
def patch_issue(
    issue_id: int,
    request: IssuePatchRequest,
    db: Session = Depends(get_db),
):
    issue = db.get(Issue, issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    return update_issue(db, issue, request)

@router.put("", response_model=IssueResponse)
def create_or_update_issue(
    request: IssuePutRequest,
    db: Session = Depends(get_db),
):
    # Fetch issue source, project, and key
    try:
        source, project, key = issue_source_project_key_from_url(request.url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    # Get or create the issue model
    issue = get_or_create(
        db,
        Issue,
        filter_kwargs={
            "source": source,
            "project": project,
            "key": key,
        },
    )

    # Add any fields to be updated and commit
    return update_issue(db, issue, request)
