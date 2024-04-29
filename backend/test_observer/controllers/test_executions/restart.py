from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from test_observer.controllers.artefacts.models import TestExecutionDTO
from test_observer.data_access.models import TestExecution
from test_observer.data_access.setup import get_db

router = APIRouter()


class RestartRequest(BaseModel):
    test_execution_id: int


@router.post("/restart")
def create_a_restart_request(request: RestartRequest, db: Session = Depends(get_db)):
    te = db.get(TestExecution, request.test_execution_id)
    if not te:
        msg = f"No test execution with id {request.test_execution_id} found"
        raise HTTPException(status_code=404, detail=msg)


@router.get("/restart", response_model=list[TestExecutionDTO])
def get_test_executions_to_restart():
    return []
