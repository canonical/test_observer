import csv
from datetime import datetime, timedelta
from io import StringIO

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from test_observer.controllers.reports.reports import TESTRESULTS_REPORT_COLUMNS
from test_observer.data_access.models import TestResult
from tests.helpers import (
    create_artefact,
    create_artefact_build,
    create_environment,
    create_test_case,
    create_test_execution,
    create_test_result,
)


def test_get_testresults_report_in_range(db_session: Session, test_client: TestClient):
    artefact = create_artefact(db_session, "beta")
    artefact_build = create_artefact_build(db_session, artefact)
    environment = create_environment(db_session)
    test_execution = create_test_execution(db_session, artefact_build, environment)
    test_case = create_test_case(db_session)
    test_result = create_test_result(db_session, test_case, test_execution)

    response = test_client.get(
        "/v1/reports/testresults",
        params={
            "start_date": datetime.now() - timedelta(days=1),
            "end_date": datetime.now(),
        },
    )
    content = response.content.decode()
    csv_reader = csv.reader(StringIO(content))
    column_names = next(csv_reader)
    first_row = next(csv_reader)

    assert column_names == [str(c) for c in TESTRESULTS_REPORT_COLUMNS]
    assert first_row == _expected_report_row(test_result)
    with pytest.raises(StopIteration):
        next(csv_reader)


def _expected_report_row(test_result: TestResult) -> list:
    test_case = test_result.test_case
    test_execution = test_result.test_execution
    environment = test_execution.environment
    artefact = test_execution.artefact_build.artefact
    family = artefact.stage.family
    return [
        family.name,
        artefact.name,
        artefact.version,
        artefact.status.name,
        artefact.track,
        artefact.series,
        artefact.repo,
        test_execution.status.name,
        str(test_execution.review_decision),
        test_execution.review_comment,
        environment.name,
        environment.architecture,
        test_case.name,
        test_case.category,
        test_result.status.name,
    ]
