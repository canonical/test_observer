from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from test_observer.data_access.models import ArtefactBuild
from test_observer.data_access.setup import get_db

from .models import ArtefactBuildDTO


router = APIRouter()


@router.get("/{artefact_id}/builds", response_model=list[ArtefactBuildDTO])
def get_artefact_builds(artefact_id: int, db: Session = Depends(get_db)):
    return (
        db.query(ArtefactBuild).filter(ArtefactBuild.artefact_id == artefact_id).all()
    )
