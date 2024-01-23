from collections.abc import Callable

from sqlalchemy.orm import Session

from test_observer.data_access.models import User
from test_observer.users.change_assignee import change_assignee
from tests.helpers import create_artefact


def test_change_assignee(db_session: Session, create_user: Callable[..., User]):
    artefact = create_artefact(db_session, "beta")
    user1 = create_user(
        launchpad_email="user1@email.com",
        launchpad_handle="user1",
        name="User 1",
    )
    user2 = create_user(
        launchpad_email="user2@email.com",
        launchpad_handle="user2",
        name="User 2",
    )
    artefact.assignee = user1
    db_session.commit()

    change_assignee(artefact.id, user2.id, db_session)

    assert artefact.assignee == user2
