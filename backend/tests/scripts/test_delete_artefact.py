from sqlalchemy.orm import Session

from scripts.delete_artefact import delete_artefact
from test_observer.data_access.models import Artefact
from tests.helpers import create_artefact


def test_deletes_artefact(db_session: Session):
    artefact = create_artefact(db_session, "beta")

    delete_artefact(artefact.id, db_session)

    assert db_session.get(Artefact, artefact.id) is None
