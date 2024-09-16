from fastapi import APIRouter

from . import reported_issues

router = APIRouter(tags=["environments"])
router.include_router(reported_issues.router)
