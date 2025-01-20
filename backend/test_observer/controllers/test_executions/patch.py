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


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from test_observer.controllers.artefacts.models import TestExecutionDTO
from test_observer.data_access.models import TestExecution
from test_observer.data_access.models_enums import TestExecutionStatus, TestResultStatus
from test_observer.data_access.setup import get_db

from .models import TestExecutionsPatchRequest

router = APIRouter()


@router.patch("/{id}", response_model=TestExecutionDTO)
def patch_test_execution(
    id: int,
    request: TestExecutionsPatchRequest,
    db: Session = Depends(get_db),
):
    test_execution = db.get(TestExecution, id)

    if test_execution is None:
        raise HTTPException(status_code=404, detail="TestExecution not found")

    if request.c3_link is not None:
        test_execution.c3_link = str(request.c3_link)

    if request.ci_link is not None:
        test_execution.ci_link = str(request.ci_link)

    _set_test_execution_status(request, test_execution)

    db.commit()
    return test_execution


def _set_test_execution_status(
    request: TestExecutionsPatchRequest, test_execution: TestExecution
) -> None:
    match (request.status, test_execution.test_results):
        case (TestExecutionStatus(), _):
            test_execution.status = request.status
        case ("COMPLETED", []):
            test_execution.status = TestExecutionStatus.ENDED_PREMATURELY
        case ("COMPLETED", results) if any(
            r.status == TestResultStatus.FAILED for r in results
        ):
            test_execution.status = TestExecutionStatus.FAILED
        case ("COMPLETED", _):
            test_execution.status = TestExecutionStatus.PASSED
