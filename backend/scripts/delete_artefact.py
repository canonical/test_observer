from argparse import ArgumentParser

from sqlalchemy.orm import Session

from test_observer.data_access.models import Artefact
from test_observer.data_access.setup import SessionLocal


def delete_artefact(artefact_id: int, session: Session | None = None):
    if session is None:
        session = SessionLocal()
        try:
            _delete(artefact_id, session)
        finally:
            session.close()
    else:
        _delete(artefact_id, session)


def _delete(artefact_id: int, session: Session) -> None:
    artefact = session.get(Artefact, artefact_id)
    if artefact:
        session.delete(artefact)
        session.commit()


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="delete_artefact",
        description="Given an artefact id, deletes this artefact",
        epilog="Note that this will also delete builds, test executions"
        " and test results belonging to the artefact",
    )

    parser.add_argument("artefact_id", type=int)

    args = parser.parse_args()

    delete_artefact(args.artefact_id)
