from fastapi import APIRouter

from . import auth

router = APIRouter(tags=["auth"])
router.include_router(auth.router)
