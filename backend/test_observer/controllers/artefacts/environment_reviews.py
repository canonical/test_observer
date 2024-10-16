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
    ArtefactBuildEnvironmentReviewDTO,
    EnvironmentReviewPatch,
)

router = APIRouter(tags=["environment-reviews"])


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
    return [
        review
        for build in artefact.latest_builds
        for review in build.environment_reviews
    ]


@router.patch(
    "/{artefact_id}/environment-reviews/{review_id}",
    response_model=ArtefactBuildEnvironmentReviewDTO,
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
