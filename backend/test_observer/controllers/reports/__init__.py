from fastapi import APIRouter

from . import test_results
from . import test_executions

router = APIRouter(tags=["reports"])
router.include_router(test_results.router)
router.include_router(test_executions.router)
