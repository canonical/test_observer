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

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import SecurityScopes
from sqlalchemy import delete, literal, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session, selectinload

from test_observer.common.metric_collectors import update_triaged_results_metric
from test_observer.common.permissions import Permission, permission_checker
from test_observer.controllers.applications.application_injection import (
    get_current_application,
)
from test_observer.controllers.test_results.filter_test_results import (
    filter_test_results,
)
from test_observer.data_access.models import (
    Application,
    ArtefactBuild,
    Issue,
    IssueTestResultAttachment,
    IssueTestResultAttachmentRule,
    TestExecution,
    TestResult,
    User,
)
from test_observer.data_access.setup import get_db
from test_observer.users.user_injection import get_current_user

from .models import (
    IssueAttachmentRequest,
    IssueResponse,
)

router = APIRouter()


def load_test_results_with_relations(db: Session, test_result_ids: list[int] | set[int]) -> list[TestResult]:
    """Load test results with all necessary relationships for metric updates."""
    return (
        db.query(TestResult)
        .filter(TestResult.id.in_(test_result_ids))
        .options(
            selectinload(TestResult.test_execution)
            .selectinload(TestExecution.artefact_build)
            .selectinload(ArtefactBuild.artefact),
            selectinload(TestResult.test_execution).selectinload(TestExecution.test_plan),
            selectinload(TestResult.test_case),
        )
        .all()
    )


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
        test_results = load_test_results_with_relations(db, test_result_ids)

        if detach:
            db.execute(
                delete(IssueTestResultAttachment).where(
                    IssueTestResultAttachment.issue_id == issue_id,
                    IssueTestResultAttachment.test_result_id.in_(test_result_ids),
                )
            )

            for test_result in test_results:
                update_triaged_results_metric(test_result, issue, increment=False)
        else:
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

            for test_result in test_results:
                update_triaged_results_metric(test_result, issue, increment=True)

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

        filtered_result_ids = [row[0] for row in db.execute(select(filtered_ids_query.c.id)).all()]
        test_results = load_test_results_with_relations(db, filtered_result_ids)

        if detach:
            db.execute(
                delete(IssueTestResultAttachment).where(
                    IssueTestResultAttachment.issue_id == issue_id,
                    IssueTestResultAttachment.test_result_id.in_(select(filtered_ids_query.c.id)),
                )
            )

            for test_result in test_results:
                update_triaged_results_metric(test_result, issue, increment=False)
        else:
            insert_select = select(
                literal(issue_id).label("issue_id"),
                filtered_ids_query.c.id.label("test_result_id"),
                literal(request.attachment_rule).label("attachment_rule_id"),
            )
            db.execute(
                pg_insert(IssueTestResultAttachment)
                .from_select(["issue_id", "test_result_id", "attachment_rule_id"], insert_select)
                .on_conflict_do_nothing()
            )

            for test_result in test_results:
                update_triaged_results_metric(test_result, issue, increment=True)

    # Save the result
    db.commit()
    db.refresh(issue)
    return issue


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
        Security(require_bulk_permission, scopes=[Permission.change_issue_attachment_bulk]),
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
        Security(require_bulk_permission, scopes=[Permission.change_issue_attachment_bulk]),
    ],
)
def remove_issue_attachments(
    issue_id: int,
    request: IssueAttachmentRequest,
    db: Session = Depends(get_db),
):
    return modify_issue_attachments(db, issue_id, request, detach=True)
