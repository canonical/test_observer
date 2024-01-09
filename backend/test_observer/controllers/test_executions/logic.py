from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from test_observer.common.constants import HISTORIC_TEST_RESULT_COUNT
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    TestCase,
    TestExecution,
    TestResult,
)
from test_observer.data_access.models_enums import TestExecutionStatus, TestResultStatus
from test_observer.data_access.repository import get_or_create

from .models import C3TestResult, C3TestResultStatus


def compute_test_execution_status(
    test_results: list[TestResult],
) -> TestExecutionStatus:
    failed = any(r.status == TestResultStatus.FAILED for r in test_results)
    status = TestExecutionStatus.FAILED if failed else TestExecutionStatus.PASSED
    return status


def store_test_results(
    db: Session,
    c3_test_results: list[C3TestResult],
    test_execution: TestExecution,
):
    for r in c3_test_results:
        test_case = get_or_create(
            db,
            TestCase,
            filter_kwargs={"name": r.name},
            creation_kwargs={"category": r.category},
        )

        test_result = TestResult(
            test_case=test_case,
            test_execution=test_execution,
            status=parse_c3_test_result_status(r.status),
            comment=r.comment,
            io_log=r.io_log,
        )

        db.add(test_result)

    db.commit()


def parse_c3_test_result_status(status: C3TestResultStatus) -> TestResultStatus:
    match status:
        case C3TestResultStatus.PASS:
            return TestResultStatus.PASSED
        case C3TestResultStatus.FAIL:
            return TestResultStatus.FAILED
        case C3TestResultStatus.SKIP:
            return TestResultStatus.SKIPPED


def get_matching_artefact_build_ids(
    session: Session,
    artefact: Artefact,
    architecture: str,
) -> list[int]:
    artefact_build_ids = (
        session.query(ArtefactBuild.id)
        .join(ArtefactBuild.artefact)
        .filter(
            Artefact.name == artefact.name,
            Artefact.track == artefact.track,
            Artefact.repo == artefact.repo,
            Artefact.series == artefact.series,
            ArtefactBuild.architecture == architecture,
        )
        .order_by(desc(ArtefactBuild.id))
        .all()
    )
    return [id[0] for id in artefact_build_ids]


def get_matching_test_execution_ids(
    session: Session,
    test_execution: TestExecution,
    matched_artefact_build_ids: list[int],
) -> list[int]:
    test_execution_ids = (
        session.query(TestExecution.id)
        .filter(
            TestExecution.artefact_build_id.in_(matched_artefact_build_ids),
            TestExecution.environment_id == test_execution.environment_id,
            TestExecution.id < test_execution.id,
        )
        .order_by(desc(TestExecution.id))
        .limit(HISTORIC_TEST_RESULT_COUNT)
        .all()
    )

    return [id[0] for id in test_execution_ids]


def get_historic_test_results(
    session: Session,
    test_execution: TestExecution,
) -> list[TestResult]:
    matched_artefact_build_ids = get_matching_artefact_build_ids(
        session=session,
        artefact=test_execution.artefact_build.artefact,
        architecture=test_execution.artefact_build.architecture,
    )
    matched_test_execution_ids = get_matching_test_execution_ids(
        session=session,
        test_execution=test_execution,
        matched_artefact_build_ids=matched_artefact_build_ids,
    )

    # It is important to have the order_by(TestResult.test_case_id) in this query
    # This is because we use the output of this function with itertools.groupby
    # which merges consecutive items by key, and needs the items sorted to group
    # everything correctly
    return (
        session.query(TestResult)
        .options(
            joinedload(TestResult.test_execution)
            .joinedload(TestExecution.artefact_build)
            .joinedload(ArtefactBuild.artefact)
        )
        .filter(TestResult.test_execution_id.in_(matched_test_execution_ids))
        .order_by(TestResult.test_case_id, desc(TestResult.id))
        .all()
    )
