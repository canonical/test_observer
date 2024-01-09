from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from test_observer.data_access.models import User
from test_observer.data_access.setup import get_db

from .models import CreateUserRequest, UserDTO

router = APIRouter()


# include_in_schema=False to hide this endpoints from docs as its internal use
@router.post("/", response_model=UserDTO, include_in_schema=False)
def add_user(request: CreateUserRequest, db: Session = Depends(get_db)):
    user = User(launchpad_handle=request.launchpad_handle)
    db.add(user)
    db.commit()

    return user
