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
from sqlalchemy.orm import Session

from test_observer.common.constants import APIErrors
from test_observer.data_access.models import Artefact, ArtefactBuild
from test_observer.data_access.models_enums import ArtefactStatus, FamilyName
from test_observer.data_access.repository import get_artefacts_by_family
from test_observer.data_access.setup import get_db

from .logic import (
    are_all_test_executions_approved,
    is_there_a_rejected_test_execution,
)
from .models import ArtefactBuildDTO, ArtefactDTO, ArtefactPatch

router = APIRouter()


@router.get("", response_model=list[ArtefactDTO])
def get_artefacts(family: FamilyName | None = None, db: Session = Depends(get_db)):
    """Get latest artefacts optionally by family"""
    artefacts = []
    order_by = (Artefact.name, Artefact.created_at)

    if family:
        artefacts = get_artefacts_by_family(
            db,
            family,
            load_stage=True,
            order_by_columns=order_by,
        )
    else:
        for family in FamilyName:
            artefacts += get_artefacts_by_family(
                db,
                family,
                load_stage=True,
                order_by_columns=order_by,
            )

    return artefacts


@router.get("/{artefact_id}", response_model=ArtefactDTO)
def get_artefact(artefact_id: int, db: Session = Depends(get_db)):
    """Get an artefact by id"""
    artefact = db.get(Artefact, artefact_id)

    if artefact is None:
        raise HTTPException(status_code=404, detail="Artefact not found")

    return artefact


@router.patch("/{artefact_id}", response_model=ArtefactDTO)
def patch_artefact(
    artefact_id: int, request: ArtefactPatch, db: Session = Depends(get_db)
):
    artefact = db.get(Artefact, artefact_id)

    if artefact is None:
        raise HTTPException(status_code=404, detail="Artefact not found")

    if (
        request.status == ArtefactStatus.APPROVED
        and not are_all_test_executions_approved(artefact)
    ):
        raise HTTPException(
            status_code=400,
            detail={
                "message": "All test executions need to be approved",
                "error": APIErrors.ARTEFACT_APPROVAL_REQUIRES_ALL_TESTEXECUTION_APPROVED,
            },
        )

    if (
        request.status == ArtefactStatus.MARKED_AS_FAILED
        and not is_there_a_rejected_test_execution(artefact)
    ):
        raise HTTPException(
            400,
            detail={
                "message": "At least one test execution needs to be rejected",
                "error": APIErrors.ARTEFACT_REJECTION_REQUIRES_ONE_TESTEXECUTION_REJECTION,
            },
        )

    artefact.status = request.status
    db.commit()
    return artefact


@router.get("/{artefact_id}/builds", response_model=list[ArtefactBuildDTO])
def get_artefact_builds(artefact_id: int, db: Session = Depends(get_db)):
    """Get latest artefact builds of an artefact together with their test executions"""
    artefact_builds = (
        db.query(ArtefactBuild)
        .filter(ArtefactBuild.artefact_id == artefact_id)
        .distinct(ArtefactBuild.architecture)
        .order_by(ArtefactBuild.architecture, ArtefactBuild.revision.desc())
        .all()
    )

    for artefact_build in artefact_builds:
        artefact_build.test_executions.sort(
            key=lambda test_execution: test_execution.id
        )

    return artefact_builds
