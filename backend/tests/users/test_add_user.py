import pytest
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from scripts.add_user import add_user
from test_observer.data_access.models import User
from test_observer.external_apis.launchpad.launchpad_api import LaunchpadAPI
from test_observer.external_apis.launchpad.models import LaunchpadUser


def test_create_user(db_session: Session):
    email = "john.doe@canonical.com"

    user = add_user(email, db_session, _FakeLaunchpadAPI())

    assert user
    assert (
        db_session.execute(
            select(User).where(
                User.launchpad_email == email,
                User.launchpad_handle == "john-doe",
                User.name == "John Doe",
            )
        ).scalar_one_or_none()
        is not None
    )


def test_email_not_in_launchpad():
    email = "john@doe.com"
    with pytest.raises(ValueError, match="Email not registered in launchpad"):
        add_user(email)


class _FakeLaunchpadAPI(LaunchpadAPI):
    def __init__(self):
        # override superclass init
        pass

    def get_user_by_email(self, email: str) -> LaunchpadUser | None:
        return LaunchpadUser(handle="john-doe", email=email, name="John Doe")
