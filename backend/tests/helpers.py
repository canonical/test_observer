from sqlalchemy.orm import Session
from src.data_access.models import Artefact, Stage


def create_artefact(db_session: Session, stage_name: str, **kwargs):
    """Create a dummy artefact"""
    stage = db_session.query(Stage).filter(Stage.name == stage_name).first()
    artefact = Artefact(
        name=kwargs.get("name", ""),
        stage=stage,
        version=kwargs.get("version", "1.1.1"),
        source=kwargs.get("source", {}),
    )
    db_session.add(artefact)
    db_session.commit()
    return artefact
