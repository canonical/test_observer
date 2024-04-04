from fastapi import APIRouter

from . import end_test, get_test_results, patch, start_test

router = APIRouter()
router.include_router(start_test.router)
router.include_router(get_test_results.router)
router.include_router(end_test.router)
router.include_router(patch.router)
