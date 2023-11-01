# Copyright 2023 Canonical Ltd.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Written by:
#        Omar Selo <omar.selo@canonical.com>
#        Nadzeya Hutsko <nadzeya.hutsko@canonical.com>
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from test_observer.data_access.models import Artefact, ArtefactBuild, TestExecution
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.repository import get_artefacts_by_family
from test_observer.data_access.setup import get_db

from .models import ArtefactBuildDTO, ArtefactDTO

router = APIRouter()


@router.get("", response_model=list[ArtefactDTO])
def get_artefacts(family: FamilyName | None = None, db: Session = Depends(get_db)):
    """Get latest artefacts optionally by family"""
    artefacts = []

    if family:
        artefacts = get_artefacts_by_family(db, family, load_stage=True)
    else:
        for family in FamilyName:
            artefacts += get_artefacts_by_family(db, family, load_stage=True)

    return artefacts


@router.get("/{artefact_id}", response_model=ArtefactDTO)
def get_artefact(artefact_id: int, db: Session = Depends(get_db)):
    """Get an artefact by id"""
    artefact = db.query(Artefact).get(artefact_id)

    if artefact is None:
        raise HTTPException(status_code=404, detail="Artefact not found")

    return artefact


@router.get("/{artefact_id}/builds", response_model=list[ArtefactBuildDTO])
def get_artefact_builds(artefact_id: int, db: Session = Depends(get_db)):
    """Get latest artefact builds of an artefact together with their test executions"""
    artefacts = (
        db.query(ArtefactBuild)
        .filter(ArtefactBuild.artefact_id == artefact_id)
        .distinct(ArtefactBuild.architecture)
        .order_by(ArtefactBuild.architecture, ArtefactBuild.revision.desc())
        .options(
            joinedload(ArtefactBuild.test_executions).joinedload(
                TestExecution.environment
            )
        )
        .all()
    )

    return artefacts
