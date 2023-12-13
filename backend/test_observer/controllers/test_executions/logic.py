from sqlalchemy.orm import Session

from test_observer.data_access.models import TestCase, TestExecution, TestResult
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
