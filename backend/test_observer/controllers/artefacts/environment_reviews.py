# Copyright (C) 2023-2025 Canonical Ltd.
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
    ArtefactBuildEnvironmentReview,
)
from test_observer.data_access.setup import get_db

from .models import (
    ArtefactBuildEnvironmentReviewResponse,
    EnvironmentReviewPatch,
)

router = APIRouter(tags=["environment-reviews"])


@router.get(
    "/{artefact_id}/environment-reviews",
    response_model=list[ArtefactBuildEnvironmentReviewResponse],
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
    return [
        review
        for build in artefact.latest_builds
        for review in build.environment_reviews
    ]


@router.patch(
    "/{artefact_id}/environment-reviews/{review_id}",
    response_model=ArtefactBuildEnvironmentReviewResponse,
)
def update_environment_review(
    artefact_id: int,
    request: EnvironmentReviewPatch,
    review_id: int,
    db: Session = Depends(get_db),
):
    review = db.scalar(
        select(ArtefactBuildEnvironmentReview)
        .where(ArtefactBuildEnvironmentReview.id == review_id)
        .options(selectinload(ArtefactBuildEnvironmentReview.artefact_build))
    )

    if not review:
        raise HTTPException(404, f"Environment review {review_id} doesn't exist")

    if review.artefact_build.artefact_id != artefact_id:
        msg = f"Environment review {review_id} doesn't belong to artefact {artefact_id}"
        raise HTTPException(422, msg)

    for field in request.model_fields_set:
        value = getattr(request, field)
        if value is not None:
            setattr(review, field, value)

    db.commit()
    return review
