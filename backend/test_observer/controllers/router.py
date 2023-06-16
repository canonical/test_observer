from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from test_observer.data_access.setup import get_db

from .application import version
from .artefacts import artefacts
from .families import families
from .promoter import promoter
from .test_execution import test_execution
from .test_executions import test_executions

router = APIRouter()
router.include_router(promoter.router)
router.include_router(test_execution.router, prefix="/v1/test-execution")
router.include_router(families.router, prefix="/v1/families")
router.include_router(version.router, prefix="/v1/version")
router.include_router(test_executions.router, prefix="/v1/test-executions")
router.include_router(artefacts.router, prefix="/v1/artefacts")


@router.get("/")
def root(db: Session = Depends(get_db)):
    db.execute(text("select 'test db connection'"))
    return "test observer api"
