from sqlalchemy import ScalarSelect, func
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.orm import Session
from test_observer.common.constants import HISTORIC_TEST_RESULT_COUNT
from test_observer.controllers.test_executions.helpers import (
    parse_historic_test_results,
)
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    TestCase,
    TestExecution,
    TestResult,
)
from test_observer.data_access.models_enums import TestExecutionStatus, TestResultStatus
from test_observer.data_access.repository import get_or_create

from .models import C3TestResult, C3TestResultStatus, HistoricTestResult


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


def _get_matching_test_executions_subquery(
    session: Session,
    test_execution: TestExecution,
) -> ScalarSelect:
    current_artefact = test_execution.artefact_build.artefact
    return (
        session.query(TestExecution.id)
        .join(TestExecution.artefact_build)
        .join(ArtefactBuild.artefact)
        .filter(
            Artefact.name == current_artefact.name,
            Artefact.track == current_artefact.track,
            Artefact.repo == current_artefact.repo,
            Artefact.series == current_artefact.series,
            TestExecution.environment_id == test_execution.environment_id,
            TestExecution.id < test_execution.id,
        )
        .limit(HISTORIC_TEST_RESULT_COUNT)
        .subquery()
        .as_scalar()
    )


def get_historic_test_results(
    session: Session,
    test_execution: TestExecution,
) -> dict[int, list[HistoricTestResult]]:
    historic_test_execution_subquery = _get_matching_test_executions_subquery(
        session=session,
        test_execution=test_execution,
    )

    historic_test_results = (
        session.query(
            TestResult.test_case_id,
            func.array_agg(aggregate_order_by(TestResult.status, TestResult.id.desc())),
            func.array_agg(aggregate_order_by(Artefact.version, TestResult.id.desc())),
        )
        .join(TestResult.test_execution)
        .join(TestExecution.artefact_build)
        .join(ArtefactBuild.artefact)
        .filter(TestResult.test_execution_id.in_(historic_test_execution_subquery))
        .group_by(TestResult.test_case_id)
        .all()
    )

    return parse_historic_test_results(historic_test_results)
