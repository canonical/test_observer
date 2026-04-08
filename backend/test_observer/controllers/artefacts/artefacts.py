# Copyright 2023 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session, selectinload

from test_observer.common.enums import Permission
from test_observer.common.permissions import (
    check_amr_permission,
    check_artefact_permission,
    openapi_scope_declaration,
    permission_checker,
)
from test_observer.controllers.applications.application_injection import (
    get_current_application,
)
from test_observer.controllers.artefacts.artefact_retriever import ArtefactRetriever
from test_observer.data_access.models import (
    Application,
    Artefact,
    ArtefactBuild,
    User,
)
from test_observer.data_access.models_enums import (
    ArtefactStatus,
    CharmStage,
    DebStage,
    FamilyName,
    ImageStage,
    SnapStage,
    StageName,
)
from test_observer.data_access.repository import get_artefacts_by_family
from test_observer.data_access.setup import get_db
from test_observer.users.user_injection import get_current_user

from . import builds, environment_reviews
from .logic import (
    are_all_environments_approved,
    is_there_a_rejected_environment,
)
from .models import (
    ArtefactHistoryItemResponse,
    ArtefactHistoryResponse,
    ArtefactPatch,
    ArtefactResponse,
    ArtefactSearchResponse,
    ArtefactVersionResponse,
)

router = APIRouter(tags=["artefacts"])


@router.get(
    "",
    response_model=list[ArtefactResponse],
    dependencies=[Security(permission_checker, scopes=[Permission.view_artefact])],
)
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


@router.get(
    "/search",
    response_model=ArtefactSearchResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_artefact])],
)
def search_artefacts(
    q: Annotated[
        str | None,
        Query(description="Search term for artefact names"),
    ] = None,
    families: Annotated[
        list[FamilyName] | None,
        Query(description="Filter by artefact families"),
    ] = None,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=1000,
            description="Maximum number of results (defaults to 50 if not specified)",
        ),
    ] = 50,
    offset: Annotated[
        int,
        Query(ge=0, description="Number of results to skip for pagination"),
    ] = 0,
    db: Session = Depends(get_db),
) -> ArtefactSearchResponse:
    """
    Search for artefacts by name with pagination support.

    Returns a list of distinct artefact names that match the search query.
    """
    query = select(distinct(Artefact.name)).where(Artefact.archived.is_(False)).order_by(Artefact.name)

    if families and len(families) > 0:
        query = query.where(Artefact.family.in_(families))

    # Apply search filter if provided
    if q and q.strip():
        search_term = f"%{q.strip()}%"
        query = query.where(Artefact.name.ilike(search_term))

    # Count total before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_count = db.execute(count_query).scalar() or 0

    # Apply pagination
    query = query.offset(offset).limit(limit)

    artefacts = db.execute(query).scalars().all()
    return ArtefactSearchResponse(
        artefacts=list(artefacts),
        count=total_count,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/history",
    response_model=ArtefactHistoryResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_artefact])],
)
def get_artefact_history(
    name: Annotated[str, Query(description="Artefact name")],
    family: Annotated[FamilyName, Query(description="Artefact family")],
    track: Annotated[str, Query(description="Artefact track")] = "latest",
    stage: Annotated[StageName | None, Query(description="Filter by stage")] = None,
    limit: Annotated[
        int, Query(ge=1, le=500, description="Maximum number of results (defaults to 10 if not specified)")
    ] = 10,
    offset: Annotated[int, Query(ge=0, description="Number of results to skip for pagination")] = 0,
    db: Session = Depends(get_db),
) -> ArtefactHistoryResponse:
    """
    Get the versioning history of an artefact for a given name, family, and track,
    optionally filtered by stage, with pagination support.

    Returns a list of artefact versions along with their creation date.
    """
    query = (
        select(Artefact)
        .where(Artefact.name == name)
        .where(Artefact.track == track)
        .where(Artefact.family == family)
        .order_by(Artefact.id.desc())
        .limit(limit)
        .offset(offset)
        .options(selectinload(Artefact.builds).selectinload(ArtefactBuild.test_executions))
    )

    if stage is not None:
        query = query.where(Artefact.stage == stage)

    artefacts = db.scalars(query).all()

    return ArtefactHistoryResponse(
        count=len(artefacts),
        items=[
            ArtefactHistoryItemResponse(
                artefact_id=artefact.id,
                name=artefact.name,
                version=artefact.version,
                stage=artefact.stage,
                created_at=artefact.created_at,
            )
            for artefact in artefacts
        ],
    )


@router.get(
    "/{artefact_id}",
    response_model=ArtefactResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_artefact])],
)
def get_artefact(
    artefact: Artefact = Depends(
        ArtefactRetriever(selectinload(Artefact.builds).selectinload(ArtefactBuild.environment_reviews))
    ),
):
    return artefact


@router.patch(
    "/{artefact_id}",
    response_model=ArtefactResponse,
    dependencies=[
        Security(openapi_scope_declaration, scopes=[Permission.change_artefact.value])
    ],
)
def patch_artefact(
    request: ArtefactPatch,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
    app: Application | None = Depends(get_current_application),
    artefact: Artefact = Depends(
        ArtefactRetriever(selectinload(Artefact.builds).selectinload(ArtefactBuild.environment_reviews))
    ),
):
    check_artefact_permission(db, user, app, artefact, Permission.change_artefact)

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
    if "jira_issue" in request.model_fields_set:
        artefact.jira_issue = request.jira_issue

    reviewer_ids_set = hasattr(request, "reviewer_ids") and "reviewer_ids" in request.model_fields_set
    reviewer_emails_set = hasattr(request, "reviewer_emails") and "reviewer_emails" in request.model_fields_set

    if reviewer_ids_set and reviewer_emails_set:
        raise HTTPException(
            status_code=422,
            detail="Cannot specify both reviewer_ids and reviewer_emails",
        )

    # Handle reviewer_ids
    if reviewer_ids_set:
        if request.reviewer_ids is None:
            artefact.reviewers = []
        elif len(request.reviewer_ids) != len(set(request.reviewer_ids)):
            raise HTTPException(
                status_code=422,
                detail="Duplicate user ids are not allowed in reviewer_ids",
            )
        else:
            reviewers = []
            users_by_id = {
                user.id: user for user in db.scalars(select(User).where(User.id.in_(request.reviewer_ids))).all()
            }
            for user_id in request.reviewer_ids:
                user = users_by_id.get(user_id)
                if user is None:
                    raise HTTPException(
                        status_code=422,
                        detail=f"User with id {user_id} not found",
                    )
                reviewers.append(user)
            artefact.reviewers = reviewers

    # Handle reviewer_emails
    if reviewer_emails_set:
        if request.reviewer_emails is None:
            artefact.reviewers = []
        elif len(request.reviewer_emails) != len(set(request.reviewer_emails)):
            raise HTTPException(
                status_code=422,
                detail="Duplicate user emails are not allowed in reviewer_emails",
            )
        else:
            reviewers = []
            users_by_email = {
                user.email: user
                for user in db.scalars(select(User).where(User.email.in_(request.reviewer_emails))).all()
            }
            for email in request.reviewer_emails:
                user = users_by_email.get(email)
                if user is None:
                    raise HTTPException(
                        status_code=422,
                        detail=f"User with email '{email}' not found",
                    )
                reviewers.append(user)
            artefact.reviewers = reviewers

    db.commit()
    return artefact


def _validate_artefact_status(artefact: Artefact, request: ArtefactPatch) -> None:
    if request.status == ArtefactStatus.APPROVED and not are_all_environments_approved(artefact.latest_builds):
        raise HTTPException(status_code=400, detail="All test executions need to be approved")

    if request.status == ArtefactStatus.MARKED_AS_FAILED:
        if not is_there_a_rejected_environment(artefact.latest_builds):
            raise HTTPException(400, detail="At least one test execution needs to be rejected")

        if not (request.comment or artefact.comment):
            raise HTTPException(400, detail="Can't reject an artefact without a comment")


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


@router.get(
    "/{artefact_id}/versions",
    response_model=list[ArtefactVersionResponse],
    dependencies=[Security(permission_checker, scopes=[Permission.view_artefact])],
)
def get_artefact_versions(artefact: Artefact = Depends(ArtefactRetriever()), db: Session = Depends(get_db)):
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


router.include_router(environment_reviews.router)
router.include_router(builds.router)
