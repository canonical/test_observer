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


from fastapi import APIRouter, Depends, Security, HTTPException
from fastapi.security import SecurityScopes
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import delete, select, literal
from sqlalchemy.dialects.postgresql import insert as pg_insert

from test_observer.common.permissions import Permission, permission_checker
from test_observer.common.metrics import test_executions_results_triaged
from test_observer.common.metrics_helpers import get_common_metric_labels
from test_observer.controllers.test_results.filter_test_results import (
    filter_test_results,
)
from test_observer.data_access.setup import get_db
from test_observer.data_access.models import (
    ArtefactBuild,
    Issue,
    IssueTestResultAttachment,
    TestExecution,
    TestResult,
    IssueTestResultAttachmentRule,
)
from test_observer.controllers.applications.application_injection import (
    get_current_application,
)
from test_observer.data_access.models import Application, User
from test_observer.users.user_injection import get_current_user
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

    # Retrieve the attachment rule
    if request.attachment_rule is not None:
        attachment_rule = db.get(IssueTestResultAttachmentRule, request.attachment_rule)
        if attachment_rule is None:
            raise HTTPException(status_code=404, detail="Attachment rule not found")

    # Add or remove any requested test result attachments
    if request.test_results is not None and len(request.test_results) > 0:
        test_result_ids = set(request.test_results)
        if detach:
            # Get test results before detaching to update metrics
            test_results = (
                db.query(TestResult)
                .filter(TestResult.id.in_(test_result_ids))
                .options(
                    selectinload(TestResult.test_execution)
                    .selectinload(TestExecution.artefact_build)
                    .selectinload(ArtefactBuild.artefact),
                    selectinload(TestResult.test_execution).selectinload(
                        TestExecution.test_plan
                    ),
                    selectinload(TestResult.test_case),
                )
                .all()
            )
            
            db.execute(
                delete(IssueTestResultAttachment).where(
                    IssueTestResultAttachment.issue_id == issue_id,
                    IssueTestResultAttachment.test_result_id.in_(test_result_ids),
                )
            )
            
            # Decrement triaged metric for detached results
            for test_result in test_results:
                _update_triaged_metric(issue, test_result, increment=False)
        else:
            # Get test results to update metrics after attaching
            test_results = (
                db.query(TestResult)
                .filter(TestResult.id.in_(test_result_ids))
                .options(
                    selectinload(TestResult.test_execution)
                    .selectinload(TestExecution.artefact_build)
                    .selectinload(ArtefactBuild.artefact),
                    selectinload(TestResult.test_execution).selectinload(
                        TestExecution.test_plan
                    ),
                    selectinload(TestResult.test_case),
                )
                .all()
            )
            
            db.execute(
                pg_insert(IssueTestResultAttachment)
                .values(
                    [
                        {
                            "issue_id": issue_id,
                            "test_result_id": test_result_id,
                            "attachment_rule_id": request.attachment_rule,
                        }
                        for test_result_id in test_result_ids
                    ]
                )
                .on_conflict_do_nothing()
            )
            
            # Increment triaged metric for attached results
            for test_result in test_results:
                _update_triaged_metric(issue, test_result, increment=True)

    # Add or remove any test results matching the provided filters
    if request.test_results_filters is not None:
        filters = request.test_results_filters
        if not filters.has_filters():
            raise HTTPException(
                status_code=422,
                detail="At least one filter must be provided in test_results_filters",
            )
        base_query = select(TestResult.id)
        filtered_ids_query = filter_test_results(base_query, filters).subquery()
        
        # Get the filtered test result IDs
        filtered_result_ids = [
            row[0] for row in db.execute(select(filtered_ids_query.c.id)).all()
        ]
        
        if detach:
            # Get test results before detaching to update metrics
            test_results = (
                db.query(TestResult)
                .filter(TestResult.id.in_(filtered_result_ids))
                .options(
                    selectinload(TestResult.test_execution)
                    .selectinload(TestExecution.artefact_build)
                    .selectinload(ArtefactBuild.artefact),
                    selectinload(TestResult.test_execution).selectinload(
                        TestExecution.test_plan
                    ),
                    selectinload(TestResult.test_case),
                )
                .all()
            )
            
            db.execute(
                delete(IssueTestResultAttachment).where(
                    IssueTestResultAttachment.issue_id == issue_id,
                    IssueTestResultAttachment.test_result_id.in_(
                        select(filtered_ids_query.c.id)
                    ),
                )
            )
            
            # Decrement triaged metric for detached results
            for test_result in test_results:
                _update_triaged_metric(issue, test_result, increment=False)
        else:
            insert_select = select(
                literal(issue_id).label("issue_id"),
                filtered_ids_query.c.id.label("test_result_id"),
                literal(request.attachment_rule).label("attachment_rule_id"),
            )
            db.execute(
                pg_insert(IssueTestResultAttachment)
                .from_select(
                    ["issue_id", "test_result_id", "attachment_rule_id"], insert_select
                )
                .on_conflict_do_nothing()
            )
            
            # Get test results after attaching to update metrics
            test_results = (
                db.query(TestResult)
                .filter(TestResult.id.in_(filtered_result_ids))
                .options(
                    selectinload(TestResult.test_execution)
                    .selectinload(TestExecution.artefact_build)
                    .selectinload(ArtefactBuild.artefact),
                    selectinload(TestResult.test_execution).selectinload(
                        TestExecution.test_plan
                    ),
                    selectinload(TestResult.test_case),
                )
                .all()
            )
            
            # Increment triaged metric for attached results
            for test_result in test_results:
                _update_triaged_metric(issue, test_result, increment=True)

    # Save the result
    db.commit()
    db.refresh(issue)
    return issue


def _update_triaged_metric(
    issue: Issue, test_result: TestResult, increment: bool = True
) -> None:
    """Update Prometheus metric for triaged test results."""
    test_execution = test_result.test_execution
    artefact_family = test_execution.artefact_build.artefact.family
    
    # Only process metrics for charm family
    if artefact_family not in {"charm"}:
        return
    
    common_labels = get_common_metric_labels(test_execution)
    
    metric = test_executions_results_triaged.labels(
        **common_labels,
        test_name=test_result.test_case.name,
        status=test_result.status.value,
        issue_source=issue.source.value,
        issue_project=issue.project,
        issue_key=issue.key,
        issue_url=issue.url,
    )
    
    if increment:
        metric.inc()
    else:
        metric.dec()


def require_bulk_permission(
    request: IssueAttachmentRequest,
    security_scopes: SecurityScopes,
    user: User | None = Depends(get_current_user),
    app: Application | None = Depends(get_current_application),
):
    if (
        (request.test_results is not None and len(request.test_results) > 1)
        or (request.test_results_filters is not None)
        or (request.attachment_rule is not None)
    ):
        permission_checker(security_scopes, user, app)


@router.post(
    "/{issue_id}/attach",
    response_model=IssueResponse,
    dependencies=[
        Security(permission_checker, scopes=[Permission.change_issue_attachment]),
        Security(
            require_bulk_permission, scopes=[Permission.change_issue_attachment_bulk]
        ),
    ],
)
def add_issue_attachments(
    issue_id: int,
    request: IssueAttachmentRequest,
    db: Session = Depends(get_db),
):
    return modify_issue_attachments(db, issue_id, request, detach=False)


@router.post(
    "/{issue_id}/detach",
    response_model=IssueResponse,
    dependencies=[
        Security(permission_checker, scopes=[Permission.change_issue_attachment]),
        Security(
            require_bulk_permission, scopes=[Permission.change_issue_attachment_bulk]
        ),
    ],
)
def remove_issue_attachments(
    issue_id: int,
    request: IssueAttachmentRequest,
    db: Session = Depends(get_db),
):
    return modify_issue_attachments(db, issue_id, request, detach=True)
