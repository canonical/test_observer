from fastapi import APIRouter

from . import reported_issues

router = APIRouter(tags=["test-cases"])
router.include_router(reported_issues.router)
