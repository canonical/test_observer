from collections.abc import Iterable, Iterator
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from test_observer.controllers.artefacts.logic import TestExecutionStatusLogic
from test_observer.data_access.models import ArtefactBuild, TestExecution
from test_observer.data_access.setup import get_db
from test_observer.external_apis.c3.c3 import C3Api
from test_observer.external_apis.c3.models import (
    Report,
    SubmissionProcessingStatus,
    SubmissionStatus,
)

from .models import ArtefactBuildDTO, TestExecutionStatus

router = APIRouter()


@router.get("/{artefact_id}/builds", response_model=list[ArtefactBuildDTO])
def get_artefact_builds(
    artefact_id: int,
    c3api: Annotated[C3Api, Depends()],
    db: Session = Depends(get_db),
):
    """Get latest artefact builds of an artefact together with their test executions"""
    builds = _get_builds_from_db(artefact_id, db)

    submissions_statuses = c3api.get_submissions_statuses(_get_statuses_ids(builds))

    reports = c3api.get_reports(_get_reports_ids(submissions_statuses.values()))

    dto_builds = _construct_dto_builds(builds, submissions_statuses, reports)

    return dto_builds


def _construct_dto_builds(
    builds: list[ArtefactBuild],
    submissions_statuses: dict[int, SubmissionStatus],
    reports: dict[int, Report],
) -> Iterator[ArtefactBuildDTO]:
    for build in builds:
        dto_build = ArtefactBuildDTO.model_validate(build)
        for test_execution in dto_build.test_executions:
            test_execution.status = _derive_test_execution_status(
                test_execution.c3_link, submissions_statuses, reports
            )

        yield dto_build


def _derive_test_execution_status(
    c3_link: str | None,
    submissions_statuses: dict[int, SubmissionStatus],
    reports: dict[int, Report],
) -> TestExecutionStatus:
    if (c3_link := c3_link) is None:
        return TestExecutionStatusLogic.NO_C3_LINK
    if (status_id := _parse_status_id_from_c3_link(c3_link)) is None:
        return TestExecutionStatusLogic.NO_STATUS_ID_IN_C3_LINK
    if (submission_status := submissions_statuses[status_id]) is None:
        return TestExecutionStatusLogic.SUBMISSION_STATUS_NOT_FOUND
    if submission_status.status == SubmissionProcessingStatus.FAIL:
        return TestExecutionStatusLogic.SUBMISSION_STATUS_IS_FAIL
    if (report_id := submission_status.report_id) is None:
        return TestExecutionStatusLogic.NO_REPORT_ID_IN_SUBMISSION_STATUS
    if (report := reports[report_id]) is None:
        return TestExecutionStatusLogic.REPORT_NOT_FOUND
    if report.failed_test_count == 0:
        return TestExecutionStatusLogic.NO_FAILED_TESTS
    else:
        return TestExecutionStatusLogic.SOME_FAILED_TESTS


def _get_statuses_ids(builds: list[ArtefactBuild]) -> Iterator[int]:
    for build in builds:
        for test_execution in build.test_executions:
            c3_link = test_execution.c3_link
            if c3_link and (status_id := _parse_status_id_from_c3_link(c3_link)):
                yield status_id


def _get_reports_ids(submissions_statuses: Iterable[SubmissionStatus]) -> Iterator[int]:
    return (ss.report_id for ss in submissions_statuses if ss.report_id is not None)


def _get_builds_from_db(artefact_id: int, db: Session) -> list[ArtefactBuild]:
    orm_builds = (
        db.query(ArtefactBuild)
        .filter(ArtefactBuild.artefact_id == artefact_id)
        .distinct(ArtefactBuild.architecture)
        .order_by(ArtefactBuild.architecture, ArtefactBuild.revision.desc())
        .options(
            joinedload(ArtefactBuild.test_executions).joinedload(
                TestExecution.environment
            )
        )
        .all()
    )

    return orm_builds


def _parse_status_id_from_c3_link(c3_link: str) -> int | None:
    try:
        return int(c3_link.split("/")[-1])
    except TypeError:
        return None