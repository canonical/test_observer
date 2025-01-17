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

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from test_observer.controllers.artefacts.artefact_retriever import ArtefactRetriever
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
)
from test_observer.data_access.models_enums import ArtefactStatus, FamilyName
from test_observer.data_access.repository import get_artefacts_by_family
from test_observer.data_access.setup import get_db

from . import builds, environment_reviews
from .logic import (
    are_all_environments_approved,
    is_there_a_rejected_environment,
)
from .models import (
    ArtefactDTO,
    ArtefactPatch,
    ArtefactVersionDTO,
)

router = APIRouter(tags=["artefacts"])
router.include_router(environment_reviews.router)
router.include_router(builds.router)


@router.get("", response_model=list[ArtefactDTO])
def get_artefacts(family: FamilyName | None = None, db: Session = Depends(get_db)):
    """Get latest artefacts optionally by family"""
    artefacts = []
    order_by = (Artefact.name, Artefact.created_at)

    if family:
        artefacts = get_artefacts_by_family(
            db,
            family,
            load_environment_reviews=True,
            order_by_columns=order_by,
        )
    else:
        for family in FamilyName:
            artefacts += get_artefacts_by_family(
                db,
                family,
                load_environment_reviews=True,
                order_by_columns=order_by,
            )

    return artefacts


@router.get("/{artefact_id}", response_model=ArtefactDTO)
def get_artefact(
    artefact: Artefact = Depends(
        ArtefactRetriever(
            selectinload(Artefact.builds).selectinload(
                ArtefactBuild.environment_reviews
            )
        )
    ),
):
    return artefact


@router.patch("/{artefact_id}", response_model=ArtefactDTO)
def patch_artefact(
    request: ArtefactPatch,
    db: Session = Depends(get_db),
    artefact: Artefact = Depends(
        ArtefactRetriever(
            selectinload(Artefact.builds).selectinload(
                ArtefactBuild.environment_reviews
            )
        )
    ),
):
    _validate_artefact_status(artefact.latest_builds, request.status)

    artefact.status = request.status
    db.commit()
    return artefact


def _validate_artefact_status(
    builds: list[ArtefactBuild], status: ArtefactStatus
) -> None:
    ...
    if status == ArtefactStatus.APPROVED and not are_all_environments_approved(builds):
        raise HTTPException(
            status_code=400,
            detail="All test executions need to be approved",
        )

    if (
        status == ArtefactStatus.MARKED_AS_FAILED
        and not is_there_a_rejected_environment(builds)
    ):
        raise HTTPException(
            400,
            detail="At least one test execution needs to be rejected",
        )


@router.get("/{artefact_id}/versions", response_model=list[ArtefactVersionDTO])
def get_artefact_versions(
    artefact: Artefact = Depends(ArtefactRetriever()), db: Session = Depends(get_db)
):
    return db.scalars(
        select(Artefact)
        .where(Artefact.name == artefact.name)
        .where(Artefact.track == artefact.track)
        .where(Artefact.series == artefact.series)
        .where(Artefact.repo == artefact.repo)
        .where(Artefact.os == artefact.os)
        .where(Artefact.series == artefact.series)
        .order_by(Artefact.id.desc())
    )
