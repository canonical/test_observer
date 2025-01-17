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

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from test_observer.data_access.models import (
    TestExecution,
    TestResult,
)
from test_observer.data_access.setup import get_db

from .logic import get_previous_test_results
from .models import TestResultResponse

router = APIRouter(tags=["test-results"])


@router.get("/{id}/test-results", response_model=list[TestResultResponse])
def get_test_results(id: int, db: Session = Depends(get_db)):
    test_execution = db.get(
        TestExecution,
        id,
        options=[
            selectinload(TestExecution.test_results).selectinload(TestResult.test_case),
        ],
    )

    if test_execution is None:
        raise HTTPException(status_code=404, detail="TestExecution not found")

    previous_test_results = get_previous_test_results(db, test_execution)

    test_results: list[TestResultResponse] = []
    for test_result in test_execution.test_results:
        parsed_test_result = TestResultResponse.model_validate(test_result)
        parsed_test_result.previous_results = previous_test_results.get(
            test_result.test_case_id, []
        )
        test_results.append(parsed_test_result)

    return test_results
