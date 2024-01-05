from .models import HistoricTestResult
from test_observer.data_access.models import TestExecution


def get_historic_test_result_mapping(
    historic_test_executions: list[TestExecution],
) -> dict[int, list[HistoricTestResult]]:
    historic_test_result_mapping: dict[int, list[HistoricTestResult]] = {}
    for current_test_execution in historic_test_executions:
        for test_result in current_test_execution.test_results:
            historic_test_result_mapping[
                test_result.test_case_id
            ] = historic_test_result_mapping.get(test_result.test_case_id, [])

            historic_test_result_mapping[test_result.test_case_id].append(
                HistoricTestResult(
                    status=test_result.status,
                    version=current_test_execution.artefact_build.artefact.version,
                )
            )
    return historic_test_result_mapping
