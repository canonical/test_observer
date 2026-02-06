# Copyright 2024 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from test_observer.common.permissions import Permission, permission_checker
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
    dependencies=[Security(permission_checker, scopes=[Permission.view_environment_review])],
)
def get_environment_reviews(
    artefact: Artefact = Depends(
        ArtefactRetriever(selectinload(Artefact.builds).selectinload(ArtefactBuild.environment_reviews))
    ),
):
    return [review for build in artefact.latest_builds for review in build.environment_reviews]


@router.patch(
    "/{artefact_id}/environment-reviews/bulk",
    response_model=list[ArtefactBuildEnvironmentReviewResponse],
    dependencies=[
        Security(permission_checker, scopes=[Permission.change_environment_review])
    ],
)
def bulk_update_environment_reviews(
    artefact_id: int,
    requests: list[EnvironmentReviewPatch],
    db: Session = Depends(get_db),
):
    review_ids = [request.id for request in requests if request.id is not None]
    reviews = db.scalars(
        select(ArtefactBuildEnvironmentReview)
        .where(ArtefactBuildEnvironmentReview.id.in_(review_ids))
        .options(selectinload(ArtefactBuildEnvironmentReview.artefact_build))
    ).all()

    reviews_dict = {review.id: review for review in reviews}

    updated_reviews = []
    for request in requests:
        review = reviews_dict.get(request.id)
        if not review:
            continue

        if review.artefact_build.artefact_id != artefact_id:
            msg = (
                f"Environment review {request.id} doesn't belong to artefact "
                f"{artefact_id}"
            )
            raise HTTPException(422, msg)

        for field in request.model_fields_set:
            value = getattr(request, field)
            if value is not None:
                setattr(review, field, value)

        updated_reviews.append(review)

    db.commit()
    return updated_reviews


@router.patch(
    "/{artefact_id}/environment-reviews/{review_id}",
    response_model=ArtefactBuildEnvironmentReviewResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.change_environment_review])],
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
