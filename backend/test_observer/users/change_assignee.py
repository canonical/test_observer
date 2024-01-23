from sqlalchemy.orm import Session

from test_observer.data_access.models import Artefact, User
from test_observer.data_access.setup import SessionLocal


def change_assignee(
    artefact_id: int, user_id: int, session: Session | None = None
) -> Artefact:
    if session is None:
        session = SessionLocal()
        try:
            return _change_assignee(artefact_id, user_id, session)
        finally:
            session.close()
    else:
        return _change_assignee(artefact_id, user_id, session)


def _change_assignee(artefact_id: int, user_id: int, session: Session) -> Artefact:
    artefact = session.get(Artefact, artefact_id)
    user = session.get(User, user_id)

    if artefact is None:
        raise ValueError(f"No artefact with id {artefact_id} found")

    if user is None:
        raise ValueError(f"No user with id {user_id} found")

    artefact.assignee = user
    session.commit()
    return artefact
