# Copyright 2023 Canonical Ltd.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Written by:
#        Omar Selo <omar.selo@canonical.com>
#        Nadzeya Hutsko <nadzeya.hutsko@canonical.com>


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from test_observer.data_access.models import (
    TestExecution,
    TestResult,
)
from test_observer.data_access.setup import get_db

from .logic import get_previous_test_results
from .models import TestResultDTO

router = APIRouter()


@router.get("/{id}/test-results", response_model=list[TestResultDTO])
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

    test_results: list[TestResultDTO] = []
    for test_result in test_execution.test_results:
        parsed_test_result = TestResultDTO.model_validate(test_result)
        parsed_test_result.previous_results = previous_test_results.get(
            test_result.test_case_id, []
        )
        test_results.append(parsed_test_result)

    return test_results
