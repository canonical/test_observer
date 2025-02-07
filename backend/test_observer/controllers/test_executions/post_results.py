# Copyright (C) 2023-2025 Canonical Ltd.
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


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete
from sqlalchemy.orm import Session

from test_observer.controllers.test_executions.models import TestResultRequest
from test_observer.data_access.models import TestCase, TestExecution, TestResult
from test_observer.data_access.repository import get_or_create
from test_observer.data_access.setup import get_db

router = APIRouter(tags=["test-results"])


@router.post("/{id}/test-results")
def post_results(
    id: int,
    request: list[TestResultRequest],
    db: Session = Depends(get_db),
):
    test_execution = db.get(TestExecution, id)

    if test_execution is None:
        raise HTTPException(status_code=404, detail="TestExecution not found")

    for result in request:
        test_case = get_or_create(
            db,
            TestCase,
            filter_kwargs={"name": result.name},
            creation_kwargs={
                "category": result.category,
                "template_id": result.template_id,
            },
        )

        db.execute(
            delete(TestResult).where(
                TestResult.test_execution_id == test_execution.id,
                TestResult.test_case_id == test_case.id,
            )
        )

        test_result = TestResult(
            test_execution=test_execution,
            test_case=test_case,
            status=result.status,
            comment=result.comment,
            io_log=result.io_log,
        )

        db.add(test_result)

    db.commit()
