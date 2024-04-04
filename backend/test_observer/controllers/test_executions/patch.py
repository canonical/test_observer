from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from test_observer.controllers.artefacts.models import TestExecutionDTO
from test_observer.data_access.models import TestExecution
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

    if request.status is not None:
        test_execution.status = request.status

    if request.review_decision is not None:
        test_execution.review_decision = list(request.review_decision)

    if request.review_comment is not None:
        test_execution.review_comment = request.review_comment

    db.commit()
    return test_execution
