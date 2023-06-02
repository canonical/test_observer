from fastapi import APIRouter


router = APIRouter()


@router.patch("/:id")
def patch_test_execution():
    pass
