from itertools import groupby
from .models import HistoricTestResult
from test_observer.data_access.models import TestResult


def parse_historic_test_results(
    historic_test_results: list[TestResult],
) -> dict[int, list[HistoricTestResult]]:
    grouped_test_cases = groupby(
        historic_test_results, lambda test_result: test_result.test_case_id
    )

    return {
        test_case_id: [
            HistoricTestResult(
                status=test_result.status,
                version=test_result.test_execution.artefact_build.artefact.version,
            )
            for test_result in test_results
        ]
        for test_case_id, test_results in grouped_test_cases
    }
