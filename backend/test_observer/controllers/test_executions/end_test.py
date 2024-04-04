from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from test_observer.data_access.models import TestExecution
from test_observer.data_access.setup import get_db

from .logic import (
    compute_test_execution_status,
    delete_previous_results,
    store_test_results,
)
from .models import EndTestExecutionRequest

router = APIRouter()


@router.put("/end-test")
def end_test_execution(request: EndTestExecutionRequest, db: Session = Depends(get_db)):
    test_execution = (
        db.query(TestExecution)
        .filter(TestExecution.ci_link == request.ci_link)
        .one_or_none()
    )

    if test_execution is None:
        raise HTTPException(status_code=404, detail="Related TestExecution not found")

    delete_previous_results(db, test_execution)
    store_test_results(db, request.test_results, test_execution)
    test_execution.status = compute_test_execution_status(test_execution.test_results)

    if request.c3_link is not None:
        test_execution.c3_link = request.c3_link

    db.commit()
