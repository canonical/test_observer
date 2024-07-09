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
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.query import RowReturningQuery


from test_observer.data_access import queries
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
    ArtefactDTO,
    ArtefactPatch,
)

router = APIRouter(tags=["artefacts"])


def _get_test_execution_counts_subquery(db: Session) -> RowReturningQuery:
    # Define subquery to count all TestExecutions for each Artefact
    all_tests = (
        db.query(
            ArtefactBuild.artefact_id,
            func.count(TestExecution.id).label("total"),
        )
        .join(TestExecution, TestExecution.artefact_build_id == ArtefactBuild.id)
        .group_by(ArtefactBuild.artefact_id)
        .subquery()
    )

    # Define subquery to count completed TestExecutions for each Artefact
    completed_tests = (
        db.query(
            ArtefactBuild.artefact_id,
            func.count(TestExecution.id).label("completed"),
        )
        .join(TestExecution, TestExecution.artefact_build_id == ArtefactBuild.id)
        .filter(func.array_length(TestExecution.review_decision, 1) > 0)
        .group_by(ArtefactBuild.artefact_id)
        .subquery()
    )

    # Define subquery to calculate the ratio of completed TestExecutions to all TestExecutions
    return (
        db.query(
            all_tests.c.artefact_id,
            func.coalesce(all_tests.c.total, 0).label("total"),
            func.coalesce(completed_tests.c.completed, 0).label("completed"),
        )
        .outerjoin(
            completed_tests, all_tests.c.artefact_id == completed_tests.c.artefact_id
        )
        .subquery()
    )


def _get_artefact_from_db(artefact_id: int, db: Session = Depends(get_db)) -> Artefact:
    a = db.get(Artefact, artefact_id)
    if a is None:
        msg = f"Artefact with id {artefact_id} not found"
        raise HTTPException(status_code=404, detail=msg)
    return a


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

    test_execution_counts = _get_test_execution_counts_subquery(db)

    # Execute the query and fetch all results
    results = (
        db.query(
            Artefact.id,
            test_execution_counts.c.total,
            test_execution_counts.c.completed,
        )
        .outerjoin(
            test_execution_counts, Artefact.id == test_execution_counts.c.artefact_id
        )
        .filter(Artefact.id.in_([artefact.id for artefact in artefacts]))
        .all()
    )

    # Convert the results to a dictionary
    counts_dict = {
        artefact_id: {
            "total": total,
            "completed": completed,
        }
        for artefact_id, total, completed in results
    }

    # Add the ratio_completed to the artefacts
    for artefact in artefacts:
        if counts_dict.get(artefact.id):
            artefact.all_test_executions_count = counts_dict[artefact.id]["total"]
            artefact.completed_test_executions_count = counts_dict[artefact.id][
                "completed"
            ]

    return artefacts


@router.get("/{artefact_id}", response_model=ArtefactDTO)
def get_artefact(artefact: Artefact = Depends(_get_artefact_from_db)):
    return artefact


@router.patch("/{artefact_id}", response_model=ArtefactDTO)
def patch_artefact(
    request: ArtefactPatch,
    db: Session = Depends(get_db),
    artefact: Artefact = Depends(_get_artefact_from_db),
):
    latest_builds = list(
        db.scalars(
            queries.latest_artefact_builds.where(
                ArtefactBuild.artefact_id == artefact.id
            ).options(joinedload(ArtefactBuild.test_executions))
        ).unique()
    )

    _validate_artefact_status(latest_builds, request.status)

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
def get_artefact_builds(artefact_id: int, db: Session = Depends(get_db)):
    """Get latest artefact builds of an artefact together with their test executions"""
    latest_builds = list(
        db.scalars(
            queries.latest_artefact_builds.where(
                ArtefactBuild.artefact_id == artefact_id
            ).options(
                joinedload(ArtefactBuild.test_executions).joinedload(
                    TestExecution.rerun_request
                )
            )
        ).unique()
    )

    for artefact_build in latest_builds:
        artefact_build.test_executions.sort(
            key=lambda test_execution: test_execution.environment.name
        )

    return latest_builds
