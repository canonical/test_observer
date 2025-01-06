from sqlalchemy.orm import Session

from test_observer.data_access.models import User
from test_observer.data_access.setup import SessionLocal
from test_observer.external_apis.launchpad.launchpad_api import LaunchpadAPI
from test_observer.external_apis.launchpad.models import LaunchpadUser


def add_user(
    launchpad_email: str,
    session: Session | None = None,
    launchpad_api: LaunchpadAPI | None = None,
):
    if not launchpad_api:
        launchpad_api = LaunchpadAPI()

    launchpad_user = launchpad_api.get_user_by_email(launchpad_email)
    if not launchpad_user:
        raise ValueError("Email not registered in launchpad")

    if session is None:
        session = SessionLocal()
        try:
            return _create_user(launchpad_user, session)
        finally:
            session.close()
    else:
        return _create_user(launchpad_user, session)


def _create_user(launchpad_user: LaunchpadUser, session: Session) -> User:
    user = User(
        launchpad_handle=launchpad_user.handle,
        launchpad_email=launchpad_user.email,
        name=launchpad_user.name,
    )
    session.add(user)
    session.commit()
    return user
