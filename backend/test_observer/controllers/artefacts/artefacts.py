# Copyright (C) 2023 Canonical Ltd.
#
# This file is part of Test Observer Backend.
#
# Test Observer Backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# Test Observer Backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from test_observer.controllers.artefacts.artefact_retriever import ArtefactRetriever
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    User,
)
from test_observer.data_access.models_enums import (
    ArtefactStatus,
    FamilyName,
    StageName,
    SnapStage,
    DebStage,
    CharmStage,
    ImageStage,
)
from test_observer.data_access.repository import get_artefacts_by_family
from test_observer.data_access.setup import get_db

from . import builds, environment_reviews
from .logic import (
    are_all_environments_approved,
    is_there_a_rejected_environment,
)
from .models import (
    ArtefactResponse,
    ArtefactPatch,
    ArtefactVersionResponse,
)

router = APIRouter(tags=["artefacts"])
router.include_router(environment_reviews.router)
router.include_router(builds.router)


@router.get("", response_model=list[ArtefactResponse])
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


@router.get("/{artefact_id}", response_model=ArtefactResponse)
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


@router.patch("/{artefact_id}", response_model=ArtefactResponse)
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
    if request.status is not None:
        _validate_artefact_status(artefact, request)
        artefact.status = request.status
    if request.archived is not None:
        artefact.archived = request.archived
    if request.stage is not None:
        _validate_artefact_stage(artefact, request.stage)
        artefact.stage = request.stage
    if request.comment is not None:
        artefact.comment = request.comment

    assignee_id_set = (
        hasattr(request, "assignee_id") and "assignee_id" in request.model_fields_set
    )
    assignee_email_set = (
        hasattr(request, "assignee_email")
        and "assignee_email" in request.model_fields_set
    )

    if assignee_id_set and assignee_email_set:
        raise HTTPException(
            status_code=422,
            detail="Cannot specify both assignee_id and assignee_email",
        )

    if assignee_id_set:
        if request.assignee_id is None:
            artefact.assignee = None
        else:
            user = db.get(User, request.assignee_id)
            if user is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"User with id {request.assignee_id} not found",
                )
            artefact.assignee = user

    if assignee_email_set:
        if request.assignee_email is None:
            artefact.assignee = None
        else:
            user = db.scalar(
                select(User).where(User.launchpad_email == request.assignee_email)
            )
            if user is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"User with email '{request.assignee_email}' not found",
                )
            artefact.assignee = user

    db.commit()
    return artefact


def _validate_artefact_status(artefact: Artefact, request: ArtefactPatch) -> None:
    if request.status == ArtefactStatus.APPROVED and not are_all_environments_approved(
        artefact.latest_builds
    ):
        raise HTTPException(
            status_code=400, detail="All test executions need to be approved"
        )

    if request.status == ArtefactStatus.MARKED_AS_FAILED:
        if not is_there_a_rejected_environment(artefact.latest_builds):
            raise HTTPException(
                400, detail="At least one test execution needs to be rejected"
            )

        if not (request.comment or artefact.comment):
            raise HTTPException(
                400, detail="Can't reject an artefact without a comment"
            )


def _validate_artefact_stage(artefact: Artefact, stage: StageName) -> None:
    try:
        match artefact.family:
            case FamilyName.snap:
                SnapStage(stage)
            case FamilyName.deb:
                DebStage(stage)
            case FamilyName.charm:
                CharmStage(stage)
            case FamilyName.image:
                ImageStage(stage)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Stage {stage} is invalid for artefact family {artefact.family}",
        ) from e


@router.get("/{artefact_id}/versions", response_model=list[ArtefactVersionResponse])
def get_artefact_versions(
    artefact: Artefact = Depends(ArtefactRetriever()), db: Session = Depends(get_db)
):
    return db.scalars(
        select(Artefact)
        .where(Artefact.name == artefact.name)
        .where(Artefact.track == artefact.track)
        .where(Artefact.branch == artefact.branch)
        .where(Artefact.series == artefact.series)
        .where(Artefact.repo == artefact.repo)
        .where(Artefact.os == artefact.os)
        .where(Artefact.release == artefact.release)
        .order_by(Artefact.id.desc())
    )
