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
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql.base import ExecutableOption

from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    TestExecution,
)
from test_observer.data_access.models_enums import ArtefactStatus, FamilyName
from test_observer.data_access.repository import get_artefacts_by_family
from test_observer.data_access.setup import get_db

from .logic import (
    are_all_test_executions_approved,
    is_there_a_rejected_test_execution,
)
from .models import (
    ArtefactBuildDTO,
    ArtefactBuildEnvironmentReviewDTO,
    ArtefactDTO,
    ArtefactPatch,
    ArtefactVersionDTO,
)

router = APIRouter(tags=["artefacts"])


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
            load_test_executions=True,
            order_by_columns=order_by,
        )
    else:
        for family in FamilyName:
            artefacts += get_artefacts_by_family(
                db,
                family,
                load_stage=True,
                load_test_executions=True,
                order_by_columns=order_by,
            )

    return artefacts


@router.get("/{artefact_id}", response_model=ArtefactDTO)
def get_artefact(
    artefact: Artefact = Depends(
        ArtefactRetriever(
            selectinload(Artefact.builds).selectinload(ArtefactBuild.test_executions)
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
            selectinload(Artefact.builds).selectinload(ArtefactBuild.test_executions)
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
    if status == ArtefactStatus.APPROVED and not are_all_test_executions_approved(
        builds
    ):
        raise HTTPException(
            status_code=400,
            detail="All test executions need to be approved",
        )

    if (
        status == ArtefactStatus.MARKED_AS_FAILED
        and not is_there_a_rejected_test_execution(builds)
    ):
        raise HTTPException(
            400,
            detail="At least one test execution needs to be rejected",
        )


@router.get("/{artefact_id}/builds", response_model=list[ArtefactBuildDTO])
def get_artefact_builds(
    artefact: Artefact = Depends(
        ArtefactRetriever(
            selectinload(Artefact.builds)
            .selectinload(ArtefactBuild.test_executions)
            .options(
                selectinload(TestExecution.environment),
                selectinload(TestExecution.rerun_request),
            )
        )
    ),
):
    """Get latest artefact builds of an artefact together with their test executions"""
    for artefact_build in artefact.latest_builds:
        artefact_build.test_executions.sort(
            key=lambda test_execution: test_execution.environment.name
        )

    return artefact.latest_builds


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
        .order_by(Artefact.id.desc())
    )


@router.get(
    "/{artefact_id}/environment-reviews",
    response_model=list[ArtefactBuildEnvironmentReviewDTO],
)
def get_environment_reviews(
    artefact: Artefact = Depends(
        ArtefactRetriever(
            selectinload(Artefact.builds).selectinload(
                ArtefactBuild.environment_reviews
            )
        )
    ),
):
    return [review for build in artefact.builds for review in build.environment_reviews]
