from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.data_access.setup import get_db

from .artefacts import artefacts
from .families import families
from .test_execution import test_execution

router = APIRouter()
router.include_router(artefacts.router, prefix="/v0/artefacts")
router.include_router(test_execution.router, prefix="/v1/test-execution")
router.include_router(families.router, prefix="/v1/families")


@router.get("/")
def root(db: Session = Depends(get_db)):
    db.execute(text("select 'test db connection'"))
    return "test observer api"
