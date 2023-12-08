from test_observer.data_access.models import TestCase, TestResult
from test_observer.data_access.models_enums import TestExecutionStatus, TestResultStatus

from .models import C3TestResult, C3TestResultStatus


def compute_test_execution_status(
    test_results: list[TestResult],
) -> TestExecutionStatus:
    failed = any(r.status == C3TestResultStatus.FAIL for r in test_results)
    status = TestExecutionStatus.FAILED if failed else TestExecutionStatus.PASSED
    return status


def parse_c3_test_results(
    c3_test_results: list[C3TestResult],
) -> tuple[list[TestCase], list[TestResult]]:
    test_cases: list[TestCase] = []
    test_results: list[TestResult] = []
    for r in c3_test_results:
        test_case = TestCase(name=r.name, category=r.category)
        test_cases.append(test_case)

        test_result = TestResult(
            test_case=test_case,
            status=parse_c3_test_result_status(r.status),
            comment=r.comment,
            io_log=r.io_log,
        )
        test_results.append(test_result)

    return test_cases, test_results


def parse_c3_test_result_status(status: C3TestResultStatus) -> TestResultStatus:
    match status:
        case C3TestResultStatus.PASS:
            return TestResultStatus.PASSED
        case C3TestResultStatus.FAIL:
            return TestResultStatus.FAILED
        case C3TestResultStatus.SKIP:
            return TestResultStatus.SKIPPED
