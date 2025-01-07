from sqlalchemy.orm import Session

from scripts.delete_artefact import delete_artefact
from test_observer.data_access.models import Artefact
from test_observer.data_access.models_enums import StageName
from tests.data_generator import DataGenerator


def test_deletes_artefact(db_session: Session, generator: DataGenerator):
    artefact = generator.gen_artefact(StageName.beta)

    delete_artefact(artefact.id, db_session)

    assert db_session.get(Artefact, artefact.id) is None
