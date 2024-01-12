from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from test_observer.data_access.models import User
from test_observer.data_access.setup import get_db
from test_observer.external_apis.launchpad.launchpad_api import LaunchpadAPI

from .models import CreateUserRequest, UserDTO

router = APIRouter()


# include_in_schema=False to hide this endpoints from docs as its internal use
@router.post("", response_model=UserDTO, include_in_schema=False)
def add_user(
    request: CreateUserRequest,
    db: Session = Depends(get_db),
    launchpad_api: LaunchpadAPI = Depends(LaunchpadAPI),
):
    launchpad_user = launchpad_api.get_user_by_email(request.launchpad_email)

    if not launchpad_user:
        raise HTTPException(status_code=422, detail="Email not registered in launchpad")

    user = User(
        launchpad_handle=launchpad_user.handle,
        launchpad_email=launchpad_user.email,
        name=launchpad_user.name,
    )
    db.add(user)
    db.commit()

    return user
