from importlib.metadata import version, PackageNotFoundError
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.get("/")
async def get_version():
    try:
        return {"version": version(__package__)}
    except PackageNotFoundError:
        return {"version": "0.0.0"}