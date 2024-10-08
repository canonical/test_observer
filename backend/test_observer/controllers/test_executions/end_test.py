# Copyright 2024 Canonical Ltd.
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

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    ArtefactBuildEnvironmentReview,
    TestCase,
    TestExecution,
    TestResult,
)
from test_observer.data_access.models_enums import (
    ArtefactBuildEnvironmentReviewDecision,
    TestExecutionReviewDecision,
    TestExecutionStatus,
    TestResultStatus,
)
from test_observer.data_access.repository import get_or_create
from test_observer.data_access.setup import get_db

from .logic import delete_previous_results
from .models import C3TestResult, C3TestResultStatus, EndTestExecutionRequest

router = APIRouter()


@router.put("/end-test")
def end_test_execution(request: EndTestExecutionRequest, db: Session = Depends(get_db)):
    test_execution = _find_related_test_execution(request, db)

    if test_execution is None:
        raise HTTPException(status_code=404, detail="Related TestExecution not found")

    delete_previous_results(db, test_execution)
    _store_test_results(db, request.test_results, test_execution)

    has_failures = test_execution.has_failures

    test_execution.status = (
        TestExecutionStatus.FAILED if has_failures else TestExecutionStatus.PASSED
    )

    prev_test_execution = _get_previous_test_execution(db, test_execution)
    environment_review = db.scalars(
        select(ArtefactBuildEnvironmentReview).where(
            ArtefactBuildEnvironmentReview.environment_id
            == test_execution.environment_id,
            ArtefactBuildEnvironmentReview.artefact_build_id
            == test_execution.artefact_build_id,
        )
    ).one()

    if prev_test_execution:
        prev_environment_review = db.scalar(
            select(ArtefactBuildEnvironmentReview).where(
                ArtefactBuildEnvironmentReview.environment_id
                == test_execution.environment_id,
                ArtefactBuildEnvironmentReview.artefact_build_id
                == prev_test_execution.artefact_build_id,
            )
        )

        if (
            prev_environment_review
            and prev_environment_review.is_approved
            and not has_failures
            and _ran_all_previously_run_cases(prev_test_execution, test_execution)
            and not environment_review.review_decision
        ):
            environment_review.review_decision = [
                ArtefactBuildEnvironmentReviewDecision.APPROVED_ALL_TESTS_PASS
            ]

    if request.c3_link is not None:
        test_execution.c3_link = request.c3_link

    test_execution.checkbox_version = request.checkbox_version

    db.commit()


def _ran_all_previously_run_cases(
    prev_test_execution: TestExecution, test_execution: TestExecution
) -> bool:
    prev_test_cases = {
        tr.test_case.name
        for tr in prev_test_execution.test_results
        if tr.status != TestResultStatus.SKIPPED
    }

    test_cases = {
        tr.test_case.name
        for tr in test_execution.test_results
        if tr.status != TestResultStatus.SKIPPED
    }

    return prev_test_cases.issubset(test_cases)


def _get_previous_test_execution(
    db: Session, test_execution: TestExecution
) -> TestExecution | None:
    artefact = test_execution.artefact_build.artefact
    prev_artefact = _get_previous_artefact(db, artefact)

    if prev_artefact is None:
        return None

    query = (
        select(TestExecution)
        .join(ArtefactBuild)
        .where(
            ArtefactBuild.artefact_id == prev_artefact.id,
            TestExecution.environment_id == test_execution.environment_id,
        )
        .order_by(ArtefactBuild.revision.desc())
        .limit(1)
        .options(
            joinedload(TestExecution.test_results).joinedload(TestResult.test_case)
        )
    )

    return db.execute(query).unique().scalar_one_or_none()


def _get_previous_artefact(db: Session, artefact: Artefact) -> Artefact | None:
    query = (
        select(Artefact)
        .where(
            Artefact.id < artefact.id,
            Artefact.name == artefact.name,
            Artefact.track == artefact.track,
            Artefact.series == artefact.series,
            Artefact.repo == artefact.repo,
        )
        .order_by(Artefact.id.desc())
        .limit(1)
    )

    return db.execute(query).scalar_one_or_none()


def _find_related_test_execution(
    request: EndTestExecutionRequest, db: Session
) -> TestExecution | None:
    return (
        db.execute(
            select(TestExecution)
            .where(TestExecution.ci_link == request.ci_link)
            .options(
                joinedload(TestExecution.artefact_build).joinedload(
                    ArtefactBuild.artefact
                )
            )
            .options(
                joinedload(TestExecution.test_results).joinedload(TestResult.test_case)
            )
        )
        .unique()
        .scalar_one_or_none()
    )


def _store_test_results(
    db: Session,
    c3_test_results: list[C3TestResult],
    test_execution: TestExecution,
) -> None:
    for r in c3_test_results:
        test_case = get_or_create(
            db,
            TestCase,
            filter_kwargs={"name": r.name},
            creation_kwargs={"category": r.category},
        )

        if r.template_id:
            test_case.template_id = r.template_id

        test_result = TestResult(
            test_case=test_case,
            test_execution=test_execution,
            status=_parse_c3_test_result_status(r.status),
            comment=r.comment,
            io_log=r.io_log,
        )

        db.add(test_result)

    db.commit()


def _parse_c3_test_result_status(status: C3TestResultStatus) -> TestResultStatus:
    match status:
        case C3TestResultStatus.PASS:
            return TestResultStatus.PASSED
        case C3TestResultStatus.FAIL:
            return TestResultStatus.FAILED
        case C3TestResultStatus.SKIP:
            return TestResultStatus.SKIPPED
