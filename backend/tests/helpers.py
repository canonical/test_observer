from datetime import datetime

from sqlalchemy.orm import Session

from test_observer.data_access.models import Artefact, Stage


def create_artefact(db_session: Session, stage_name: str, **kwargs) -> Artefact:
    """Create a dummy artefact"""
    stage = db_session.query(Stage).filter(Stage.name == stage_name).first()
    source = kwargs.get("source")
    if not source:
        if stage_name in ("edge", "beta", "candidate", "stable"):
            source = {"store": "ubuntu", "track": "latest"}
        else:
            source = {"pocket": "proposed", "series": "jammy"}

    artefact = Artefact(
        name=kwargs.get("name", ""),
        stage=stage,
        version=kwargs.get("version", "1.1.1"),
        source=source,
        created_at=kwargs.get("created_at", datetime.utcnow()),
    )
    db_session.add(artefact)
    db_session.commit()
    return artefact
