from random import choice
from datetime import datetime

from sqlalchemy.orm import Session
from test_observer.data_access.models import Artefact, Stage, ArtefactBuild
from test_observer.data_access.models_enums import FamilyName


def create_artefact(db_session: Session, stage_name: str, **kwargs):
    """Create a dummy artefact"""
    stage = db_session.query(Stage).filter(Stage.name == stage_name).first()
    artefact = Artefact(
        name=kwargs.get("name", ""),
        stage=stage,
        version=kwargs.get("version", "1.1.1"),
        source=kwargs.get("source", {}),
        created_at=kwargs.get("created_at", datetime.utcnow()),
    )
    db_session.add(artefact)
    db_session.commit()
    return artefact


def create_artefact_builds(
    db_session: Session, artefact: Artefact, num_builds: int = 5
) -> list[ArtefactBuild]:
    """
    Create a number of ArtefactBuild instances for an Artefact and add them
    to the database
    """
    architectures = ["arm64", "x86", "amd64"]

    for i in range(num_builds):
        architecture = choice(architectures)

        build = ArtefactBuild(
            architecture=architecture,
            revision=i + 1
            if artefact.stage.family.name == FamilyName.SNAP.value
            else None,
            artefact_id=artefact.id,
        )

        # Add the build to the artefact's builds
        artefact.builds.append(build)

    # Commit the changes to the database
    db_session.commit()
    return artefact.builds
