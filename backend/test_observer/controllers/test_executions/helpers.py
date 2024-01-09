from .models import HistoricTestResult
from test_observer.data_access.models_enums import TestResultStatus


def parse_historic_test_results(
    historic_test_results: list[tuple[int, list[TestResultStatus], list[str]]],
) -> dict[int, list[HistoricTestResult]]:
    historic_test_result_mapping: dict[int, list[HistoricTestResult]] = {}
    for test_case_id, statuses, versions in historic_test_results:
        historic_test_result_mapping[test_case_id] = [
            HistoricTestResult(
                status=statuses[i],
                version=versions[i],
            )
            for i in range(len(statuses))
        ]

    return historic_test_result_mapping
