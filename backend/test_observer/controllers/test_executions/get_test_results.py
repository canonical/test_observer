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
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, with_loader_criteria

from test_observer.common.permissions import Permission, permission_checker
from test_observer.data_access.models import (
    Issue,
    IssueTestResultAttachment,
    TestExecution,
    TestResult,
)
from test_observer.data_access.models_enums import IssueStatus
from test_observer.data_access.setup import get_db

from .logic import get_previous_test_results
from .shared_models import TestResultResponse

router = APIRouter(tags=["test-results"])


@router.get(
    "/{id}/test-results",
    response_model=list[TestResultResponse],
    dependencies=[Security(permission_checker, scopes=[Permission.view_test])],
)
def get_test_results(id: int, db: Session = Depends(get_db)):
    test_execution = db.get(TestExecution, id)

    if test_execution is None:
        raise HTTPException(status_code=404, detail="TestExecution not found")

    test_results_from_db = (
        db.execute(
            select(TestResult)
            .where(TestResult.test_execution_id == id)
            .order_by(TestResult.id)
            .options(
                selectinload(TestResult.test_case),
                selectinload(TestResult.issue_attachments).selectinload(
                    IssueTestResultAttachment.issue
                ),
                with_loader_criteria(
                    IssueTestResultAttachment,
                    IssueTestResultAttachment.issue_id.not_in(
                        select(Issue.id).where(Issue.status == IssueStatus.CLOSED)
                    ),
                ),
            )
        )
        .scalars()
        .all()
    )

    previous_test_results = get_previous_test_results(db, test_execution)

    test_results: list[TestResultResponse] = []
    for test_result in test_results_from_db:
        parsed_test_result = TestResultResponse.model_validate(test_result)
        parsed_test_result.previous_results = previous_test_results.get(
            test_result.test_case_id, []
        )
        test_results.append(parsed_test_result)

    return test_results
