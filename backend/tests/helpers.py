from datetime import datetime

from sqlalchemy.orm import Session

from test_observer.data_access.models import Artefact, Stage
from test_observer.data_access.models_enums import FamilyName


def create_artefact(db_session: Session, stage_name: str, **kwargs) -> Artefact:
    """Create a dummy artefact"""
    stage = db_session.query(Stage).filter(Stage.name == stage_name).first()
    family = FamilyName(stage.family.name)

    artefact = Artefact(
        name=kwargs.get("name", ""),
        stage=stage,
        version=kwargs.get("version", "1.1.1"),
        track=kwargs.get("track", "latest" if family == FamilyName.SNAP else None),
        store=kwargs.get("store", "ubuntu" if family == FamilyName.SNAP else None),
        series=kwargs.get("series", "jammy" if family == FamilyName.DEB else None),
        repo=kwargs.get("repo", "main" if family == FamilyName.DEB else None),
        created_at=kwargs.get("created_at", datetime.utcnow()),
    )
    db_session.add(artefact)
    db_session.commit()
    return artefact
