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
