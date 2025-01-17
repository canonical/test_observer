from fastapi import APIRouter

from . import (
    end_test,
    get_test_results,
    patch,
    post_results,
    reruns,
    start_test,
    status_update,
)

router = APIRouter(tags=["test-executions"])
router.include_router(start_test.router)
router.include_router(get_test_results.router)
router.include_router(end_test.router)
router.include_router(patch.router)
router.include_router(reruns.router)
router.include_router(status_update.router)
router.include_router(post_results.router)
