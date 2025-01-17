from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from test_observer.data_access.setup import get_db

from . import environments, reports, test_cases, test_executions
from .application import version
from .artefacts import artefacts

router = APIRouter()
router.include_router(version.router, prefix="/v1/version")
router.include_router(test_executions.router, prefix="/v1/test-executions")
router.include_router(artefacts.router, prefix="/v1/artefacts")
router.include_router(reports.router, prefix="/v1/reports")
router.include_router(test_cases.router, prefix="/v1/test-cases")
router.include_router(environments.router, prefix="/v1/environments")


@router.get("/")
def root(db: Session = Depends(get_db)):
    db.execute(text("select 'test db connection'"))
    return "test observer api"


@router.get("/sentry-debug")
def trigger_error():
    division_by_zero = 1 / 0
    return division_by_zero
