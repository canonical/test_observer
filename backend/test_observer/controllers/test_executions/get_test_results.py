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
