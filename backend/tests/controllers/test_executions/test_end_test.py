from fastapi.testclient import TestClient

from test_observer.data_access.models_enums import (
    TestExecutionStatus,
    TestResultStatus,
)
from tests.data_generator import DataGenerator


def test_report_test_execution_data(test_client: TestClient, generator: DataGenerator):
    c3_link = "http://c3.localhost"
    artefact = generator.gen_artefact("beta")
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build, environment, ci_link="http://localhost"
    )
    test_case = generator.gen_test_case()

    response = test_client.put(
        "/v1/test-executions/end-test",
        json={
            "id": 1,
            "ci_link": test_execution.ci_link,
            "c3_link": c3_link,
            "test_results": [
                {
                    "id": 1,
                    "name": test_case.name,
                    "status": "pass",
                    "category": test_case.category,
                    "comment": "",
                    "io_log": "",
                },
                {
                    "id": 2,
                    "name": "test-name-2",
                    "status": "skip",
                    "category": "",
                    "comment": "",
                    "io_log": "",
                },
            ],
        },
    )

    assert response.status_code == 200
    assert test_execution.status == TestExecutionStatus.PASSED
    assert test_execution.c3_link == c3_link
    assert test_execution.test_results[0].test_case.name == test_case.name
    assert test_execution.test_results[0].status == TestResultStatus.PASSED
    assert test_execution.test_results[1].test_case.name == "test-name-2"
    assert test_execution.test_results[1].status == TestResultStatus.SKIPPED


def test_end_test_is_idempotent(test_client: TestClient, generator: DataGenerator):
    artefact = generator.gen_artefact("beta")
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build, environment, ci_link="http://localhost"
    )

    for _ in range(2):
        test_client.put(
            "/v1/test-executions/end-test",
            json={
                "id": 1,
                "ci_link": test_execution.ci_link,
                "test_results": [
                    {
                        "id": 1,
                        "name": "test name",
                        "status": "pass",
                        "category": "test category",
                        "comment": "",
                        "io_log": "",
                    }
                ],
            },
        )

    assert len(test_execution.test_results) == 1
