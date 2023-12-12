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
from sqlalchemy import delete
from sqlalchemy.orm import Session, joinedload

from test_observer.controllers.test_executions.logic import (
    compute_test_execution_status,
    store_test_results,
)
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    Stage,
    TestExecution,
    TestResult,
)
from test_observer.data_access.models_enums import TestExecutionStatus
from test_observer.data_access.repository import get_or_create
from test_observer.data_access.setup import get_db

from .models import (
    EndTestExecutionRequest,
    StartTestExecutionRequest,
    TestExecutionsPatchRequest,
    TestResultDTO,
)

router = APIRouter()


@router.put("/start-test")
def start_test_execution(
    request: StartTestExecutionRequest, db: Session = Depends(get_db)
):
    stage = (
        db.query(Stage)
        .filter(
            Stage.name == request.execution_stage,
            Stage.family.has(name=request.family),
        )
        .one()
    )

    try:
        artefact = get_or_create(
            db,
            Artefact,
            filter_kwargs={
                "name": request.name,
                "version": request.version,
                "track": request.track,
                "store": request.store,
                "series": request.series,
                "repo": request.repo,
            },
            creation_kwargs={"stage_id": stage.id},
        )

        environment = get_or_create(
            db,
            Environment,
            filter_kwargs={"name": request.environment, "architecture": request.arch},
        )

        artefact_build = get_or_create(
            db,
            ArtefactBuild,
            filter_kwargs={
                "architecture": request.arch,
                "revision": request.revision,
                "artefact_id": artefact.id,
            },
        )

        test_execution = get_or_create(
            db,
            TestExecution,
            filter_kwargs={
                "environment_id": environment.id,
                "artefact_build_id": artefact_build.id,
            },
            creation_kwargs={
                "status": TestExecutionStatus.IN_PROGRESS,
                "ci_link": request.ci_link,
            },
        )

        if test_execution.ci_link != request.ci_link:
            reset_test_execution(request, db, test_execution)

        return {"id": test_execution.id}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def reset_test_execution(
    request: StartTestExecutionRequest,
    db: Session,
    test_execution: TestExecution,
):
    test_execution.status = TestExecutionStatus.IN_PROGRESS
    test_execution.ci_link = request.ci_link
    test_execution.c3_link = None
    db.execute(
        delete(TestResult).where(TestResult.test_execution_id == test_execution.id)
    )
    db.commit()


@router.put("/end-test")
def end_test_execution(request: EndTestExecutionRequest, db: Session = Depends(get_db)):
    test_execution = (
        db.query(TestExecution)
        .filter(TestExecution.ci_link == request.ci_link)
        .one_or_none()
    )

    if test_execution is None:
        raise HTTPException(status_code=404, detail="Related TestExecution not found")

    store_test_results(db, request.test_results, test_execution)
    test_execution.status = compute_test_execution_status(test_execution.test_results)
    db.commit()


@router.patch("/{id}")
def patch_test_execution(
    id: int,
    request: TestExecutionsPatchRequest,
    db: Session = Depends(get_db),
):
    test_execution = db.get(TestExecution, id)

    if test_execution is None:
        raise HTTPException(status_code=404, detail="TestExecution not found")

    if request.c3_link is not None:
        test_execution.c3_link = str(request.c3_link)

    if request.ci_link is not None:
        test_execution.ci_link = str(request.ci_link)

    if request.status is not None:
        test_execution.status = request.status

    db.commit()


@router.get("/{id}/test-results", response_model=list[TestResultDTO])
def get_test_results(id: int, db: Session = Depends(get_db)):
    test_execution = db.get(
        TestExecution,
        id,
        options=[
            joinedload(TestExecution.test_results).joinedload(TestResult.test_case),
        ],
    )

    if test_execution is None:
        raise HTTPException(status_code=404, detail="TestExecution not found")

    return test_execution.test_results
