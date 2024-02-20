from sqlalchemy.orm import Session

from test_observer.users.change_assignee import change_assignee
from tests.data_generator import DataGenerator


def test_change_assignee(db_session: Session, generator: DataGenerator):
    artefact = generator.gen_artefact("beta")
    user1 = generator.gen_user(
        launchpad_email="user1@email.com",
        launchpad_handle="user1",
        name="User 1",
    )
    user2 = generator.gen_user(
        launchpad_email="user2@email.com",
        launchpad_handle="user2",
        name="User 2",
    )
    artefact.assignee = user1
    db_session.commit()

    change_assignee(artefact.id, user2.id, db_session)

    assert artefact.assignee == user2
