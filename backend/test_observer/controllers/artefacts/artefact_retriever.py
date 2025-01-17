# Copyright (C) 2023 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

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
