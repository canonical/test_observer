from collections.abc import Iterable, Iterator

from sqlalchemy.orm import Session, joinedload

from test_observer.data_access.models import ArtefactBuild, TestExecution
from test_observer.external_apis.c3.models import (
    Report,
    SubmissionProcessingStatus,
    SubmissionStatus,
    TestResult,
)

from .models import (
    ArtefactBuildDTO,
    EnvironmentDTO,
    TestExecutionDTO,
    TestExecutionStatus,
)


class TestExecutionStatusLogic:
    NO_C3_LINK = TestExecutionStatus.IN_PROGRESS
    NO_STATUS_ID_IN_C3_LINK = TestExecutionStatus.UNKNOWN
    SUBMISSION_STATUS_NOT_FOUND = TestExecutionStatus.UNKNOWN
    SUBMISSION_STATUS_IS_FAIL = TestExecutionStatus.FAILED
    NO_REPORT_ID_IN_SUBMISSION_STATUS = TestExecutionStatus.UNKNOWN
    REPORT_NOT_FOUND = TestExecutionStatus.UNKNOWN
    NO_FAILED_TESTS = TestExecutionStatus.PASSED
    SOME_FAILED_TESTS = TestExecutionStatus.FAILED


def get_builds_from_db(artefact_id: int, db: Session) -> list[ArtefactBuild]:
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


def get_statuses_ids(builds: list[ArtefactBuild]) -> Iterator[int]:
    for build in builds:
        for test_execution in build.test_executions:
            c3_link = test_execution.c3_link
            if c3_link and (status_id := _parse_status_id_from_c3_link(c3_link)):
                yield status_id


def get_reports_ids(submissions_statuses: Iterable[SubmissionStatus]) -> Iterator[int]:
    return (ss.report_id for ss in submissions_statuses if ss.report_id is not None)


def construct_dto_builds(
    builds: list[ArtefactBuild],
    submissions_statuses: dict[int, SubmissionStatus],
    reports: dict[int, Report],
) -> Iterator[ArtefactBuildDTO]:
    for build in builds:
        test_executions_dto = []
        for test_execution in build.test_executions:
            test_executions_dto.append(
                TestExecutionDTO(
                    id=test_execution.id,
                    jenkins_link=test_execution.jenkins_link,
                    c3_link=test_execution.c3_link,
                    environment=EnvironmentDTO.model_validate(
                        test_execution.environment
                    ),
                    status=_derive_test_execution_status(
                        test_execution.c3_link, submissions_statuses, reports
                    ),
                    test_results=_derive_test_results(
                        test_execution.c3_link, submissions_statuses, reports
                    ),
                )
            )

        build_dto = ArtefactBuildDTO(
            id=build.id,
            architecture=build.architecture,
            revision=build.revision,
            test_executions=test_executions_dto,
        )

        yield build_dto


def _derive_test_results(
    c3_link: str | None,
    submissions_statuses: dict[int, SubmissionStatus],
    reports: dict[int, Report],
) -> list[TestResult]:
    if c3_link is None:
        return []
    if (status_id := _parse_status_id_from_c3_link(c3_link)) is None:
        return []
    if (submission_status := submissions_statuses.get(status_id)) is None:
        return []
    if (report_id := submission_status.report_id) is None:
        return []

    return reports[report_id].test_results


def _derive_test_execution_status(
    c3_link: str | None,
    submissions_statuses: dict[int, SubmissionStatus],
    reports: dict[int, Report],
) -> TestExecutionStatus:
    if c3_link is None:
        return TestExecutionStatusLogic.NO_C3_LINK
    if (status_id := _parse_status_id_from_c3_link(c3_link)) is None:
        return TestExecutionStatusLogic.NO_STATUS_ID_IN_C3_LINK
    if (submission_status := submissions_statuses.get(status_id)) is None:
        return TestExecutionStatusLogic.SUBMISSION_STATUS_NOT_FOUND
    if submission_status.status == SubmissionProcessingStatus.FAIL:
        return TestExecutionStatusLogic.SUBMISSION_STATUS_IS_FAIL
    if (report_id := submission_status.report_id) is None:
        return TestExecutionStatusLogic.NO_REPORT_ID_IN_SUBMISSION_STATUS
    if (report := reports.get(report_id)) is None:
        return TestExecutionStatusLogic.REPORT_NOT_FOUND
    if report.failed_test_count == 0:
        return TestExecutionStatusLogic.NO_FAILED_TESTS
    else:
        return TestExecutionStatusLogic.SOME_FAILED_TESTS


def _parse_status_id_from_c3_link(c3_link: str) -> int | None:
    try:
        if c3_link.endswith("/"):
            # In case the link ends with "/" character
            # We skip the last character
            c3_link = c3_link[:-1]

        return int(c3_link.split("/")[-1])
    except ValueError:
        return None
