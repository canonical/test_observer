# Copyright 2025 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from sqlalchemy import String, func, select
from fastapi import HTTPException
from fastapi.security import SecurityScopes
from sqlalchemy.orm import Session, selectinload

from test_observer.common.permissions import Permission, permission_checker
from test_observer.data_access.models import (
    Issue,
)
from test_observer.data_access.models_enums import IssueSource, IssueStatus
from test_observer.data_access.repository import get_or_create
from test_observer.data_access.setup import get_db
from test_observer.users.user_injection import get_current_user

from . import attachment_rules, issue_attachments
from .issue_url_parser import issue_source_project_key_from_url
from .models import (
    IssuePatchRequest,
    IssuePutRequest,
    IssueResponse,
    IssuesGetResponse,
    MinimalIssueResponse,
)
from .issue_url_parser import issue_source_project_key_from_url

from . import issue_attachments, attachment_rules

router = APIRouter(tags=["issues"])
router.include_router(issue_attachments.router)
router.include_router(attachment_rules.router)


@router.get(
    "",
    response_model=IssuesGetResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_issue])],
)
def get_issues(
    source: Annotated[
        IssueSource | None,
        Query(description="Filter by issue source (e.g., github, jira, launchpad)"),
    ] = None,
    project: Annotated[
        str | None,
        Query(description="Filter by project name"),
    ] = None,
    status: Annotated[
        IssueStatus | None,
        Query(description="Filter by issue status (e.g., open, closed, unknown)"),
    ] = None,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=1000,
            description="Maximum number of results to return (default: 50)",
        ),
    ] = 50,
    offset: Annotated[
        int,
        Query(
            ge=0,
            description="Number of results to skip for pagination (default: 0)",
        ),
    ] = 0,
    q: Annotated[
        str | None,
        Query(description="Search term for issue source, project, keys, title, and status"),
    ] = None,
    db: Session = Depends(get_db),
):
    stmt = select(Issue)
    if source:
        stmt = stmt.where(Issue.source == source)
    if project:
        stmt = stmt.where(Issue.project == project)
    if status:
        stmt = stmt.where(Issue.status == status)

    # Apply search filter if query string provided
    if q:
        # Split query into segments and filter out empty ones
        segments = [seg.lower() for seg in q.split() if seg.strip()]

        # For each segment, create a condition that matches any field
        for segment in segments:
            segment_condition = (
                Issue.id.cast(String).contains(segment)
                | Issue.source.cast(String).ilike(f"%{segment}%")
                | Issue.project.ilike(f"%{segment}%")
                | Issue.key.ilike(f"%{segment}%")
                | Issue.title.ilike(f"%{segment}%")
                | Issue.status.cast(String).ilike(f"%{segment}%")
                | Issue.url.ilike(f"%{segment}%")
            )
            stmt = stmt.where(segment_condition)

    # Order by source, project, then key for consistent pagination
    stmt = stmt.order_by(Issue.source, Issue.project, Issue.key)

    # Count total before pagination
    count_query = select(func.count()).select_from(stmt.subquery())
    total_count = db.execute(count_query).scalar() or 0

    # Apply limit and offset
    stmt = stmt.limit(limit).offset(offset)

    issues = db.execute(stmt).scalars().all()
    return IssuesGetResponse(
        issues=[MinimalIssueResponse.model_validate(issue) for issue in issues],
        count=total_count,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{issue_id}",
    response_model=IssueResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_issue])],
)
def get_issue(
    issue_id: int,
    db: Session = Depends(get_db),
):
    issue = db.get(
        Issue,
        issue_id,
        options=(selectinload(Issue.test_result_attachment_rules),),
    )
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


def update_issue(db: Session, issue: Issue, request: IssuePatchRequest):
    if request.title is not None:
        issue.title = request.title
    if request.status is not None:
        issue.status = request.status
    if request.auto_rerun_enabled is not None:
        issue.auto_rerun_enabled = request.auto_rerun_enabled
    db.commit()
    db.refresh(issue)
    return issue


@router.patch(
    "/{issue_id}",
    response_model=IssueResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.change_issue])],
)
def patch_issue(
    issue_id: int,
    request: IssuePatchRequest,
    db: Session = Depends(get_db),
):
    issue = db.get(Issue, issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    return update_issue(db, issue, request)


@router.patch(
    "/{issue_id}/auto-rerun",
    response_model=IssueResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.change_auto_rerun])],
)
def patch_issue_auto_rerun(
    issue_id: int,
    request: IssuePatchRequest,
    db: Session = Depends(get_db),
):
    issue = db.get(Issue, issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    return update_issue(db, issue, request)


@router.put(
    "",
    response_model=IssueResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.change_issue])],
)
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
