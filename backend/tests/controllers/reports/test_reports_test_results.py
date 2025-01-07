import csv
from datetime import datetime, timedelta
from io import StringIO

from fastapi.testclient import TestClient
from httpx import Response

from test_observer.controllers.reports.test_results import (
    TESTRESULTS_REPORT_COLUMNS,
)
from test_observer.data_access.models import TestResult
from tests.data_generator import DataGenerator


def test_get_testresults_report_in_range(
    test_client: TestClient, generator: DataGenerator
):
    artefact = generator.gen_artefact("beta")
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(artefact_build, environment)
    test_case = generator.gen_test_case()
    test_result = generator.gen_test_result(test_case, test_execution)

    response = test_client.get(
        "/v1/reports/test-results",
        params={
            "start_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "end_date": datetime.now().isoformat(),
        },
    )

    table = _read_csv_response(response)

    assert len(table) == 2
    assert table[0] == [str(c) for c in TESTRESULTS_REPORT_COLUMNS]
    assert table[1] == _expected_report_row(test_result)


def test_get_testresults_report_out_range(
    test_client: TestClient, generator: DataGenerator
):
    artefact = generator.gen_artefact(
        "beta", created_at=datetime.now() - timedelta(days=2)
    )
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(artefact_build, environment)
    test_case = generator.gen_test_case()
    generator.gen_test_result(test_case, test_execution)

    response = test_client.get(
        "/v1/reports/test-results",
        params={
            "start_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "end_date": datetime.now().isoformat(),
        },
    )

    table = _read_csv_response(response)

    assert len(table) == 1
    assert table[0] == [str(c) for c in TESTRESULTS_REPORT_COLUMNS]


def _read_csv_response(response: Response) -> list:
    content = response.content.decode()
    csv_reader = csv.reader(StringIO(content))
    return list(csv_reader)


def _expected_report_row(test_result: TestResult) -> list:
    test_case = test_result.test_case
    test_execution = test_result.test_execution
    environment = test_execution.environment
    artefact = test_execution.artefact_build.artefact
    return [
        artefact.family,
        str(artefact.id),
        artefact.name,
        artefact.version,
        artefact.status.name,
        artefact.track,
        artefact.series,
        artefact.repo,
        str(artefact.created_at),
        str(test_execution.id),
        test_execution.status.name,
        "" if not test_execution.c3_link else test_execution.c3_link,
        "" if not test_execution.checkbox_version else test_execution.checkbox_version,
        test_execution.test_plan,
        environment.name,
        environment.architecture,
        test_case.template_id,
        test_case.name,
        test_case.category,
        test_result.status.name,
        str(test_result.created_at),
    ]
