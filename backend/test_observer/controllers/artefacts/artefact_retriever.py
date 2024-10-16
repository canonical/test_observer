from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql.base import ExecutableOption

from test_observer.data_access.models import (
    Artefact,
)
from test_observer.data_access.setup import get_db


class ArtefactRetriever:
    def __init__(self, *options: ExecutableOption):
        self._options = options

    def __call__(self, artefact_id: int, db: Session = Depends(get_db)):
        artefact = db.scalar(
            select(Artefact).where(Artefact.id == artefact_id).options(*self._options)
        )
        if artefact is None:
            msg = f"Artefact with id {artefact_id} not found"
            raise HTTPException(status_code=404, detail=msg)
        return artefact
