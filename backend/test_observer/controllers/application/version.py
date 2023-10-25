from importlib.metadata import PackageNotFoundError, version

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def get_version():
    try:
        return {"version": version(__package__)}
    except PackageNotFoundError:
        return {"version": "0.0.0"}
