from fastapi import APIRouter


router = APIRouter()


@router.post("/start")
def start_test_execution():
    pass


@router.patch("/")
def patch_test_execution():
    pass
