from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from test_observer.data_access.models import TestExecution
from test_observer.data_access.setup import get_db

from .models import TestExecutionsPatchRequest

router = APIRouter()


@router.patch("/{id}")
def patch_test_execution(
    id: int,
    request: TestExecutionsPatchRequest,
    db: Session = Depends(get_db),
):
    test_execution = db.query(TestExecution).filter(TestExecution.id == id).one()
    test_execution.c3_link = request.c3_link
    test_execution.jenkins_link = request.jenkins_link
    test_execution.status = request.status
    db.commit()
