from test_observer.data_access.models import TestResult
from test_observer.data_access.models_enums import TestExecutionStatus, TestResultStatus

from .models import C3TestResult, C3TestResultStatus


def compute_test_execution_status(
    test_results: list[TestResult],
) -> TestExecutionStatus:
    failed = any(r.status == C3TestResultStatus.FAIL for r in test_results)
    status = TestExecutionStatus.FAILED if failed else TestExecutionStatus.PASSED
    return status


def parse_c3_test_results(c3_test_results: list[C3TestResult]) -> list[TestResult]:
    return [
        TestResult(
            c3_id=r.id,
            name=r.name,
            status=parse_c3_test_result_status(r.status),
            category=r.category,
            comment=r.comment,
            io_log=r.io_log,
        )
        for r in c3_test_results
    ]


def parse_c3_test_result_status(status: C3TestResultStatus) -> TestResultStatus:
    match status:
        case C3TestResultStatus.PASS:
            return TestResultStatus.PASSED
        case C3TestResultStatus.FAIL:
            return TestResultStatus.FAILED
        case C3TestResultStatus.SKIP:
            return TestResultStatus.SKIPPED
