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
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from test_observer.controllers.families.models import ArtefactDTO
from test_observer.data_access.models import ArtefactBuild, Family, Stage
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.setup import get_db

from .models import ArtefactBuildDTO

router = APIRouter()


@router.get("/", response_model=list[ArtefactDTO])
def get_artefacts(family: FamilyName | None = None, db: Session = Depends(get_db)):
    """Get latest artefacts by family"""
    query = db.query(Stage)
    if family:
        query = query.filter(Stage.family.has(Family.name == family))
    stages = query.all()

    return [artefact for stage in stages for artefact in stage.latest_artefacts]


@router.get("/{artefact_id}/builds", response_model=list[ArtefactBuildDTO])
def get_artefact_builds(artefact_id: int, db: Session = Depends(get_db)):
    """Get latest artefact builds of an artefact together with their test executions"""
    return (
        db.query(ArtefactBuild)
        .filter(ArtefactBuild.artefact_id == artefact_id)
        .distinct(ArtefactBuild.architecture)
        .order_by(ArtefactBuild.architecture, ArtefactBuild.revision.desc())
        .all()
    )
