from fastapi import APIRouter


router = APIRouter()


@router.put("/start")
def start_test_execution():
    pass


@router.patch("/")
def patch_test_execution():
    pass
