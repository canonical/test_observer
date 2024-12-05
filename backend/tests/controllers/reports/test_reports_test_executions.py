import csv
from datetime import datetime, timedelta
from io import StringIO

from sqlalchemy.orm import Session

from fastapi.testclient import TestClient
from httpx import Response

from test_observer.controllers.reports.test_executions import (
    TEST_EXECUTIONS_REPORT_COLUMNS,
)
from test_observer.data_access.models import (
    ArtefactBuildEnvironmentReview,
    TestExecution,
)
from tests.data_generator import DataGenerator


def test_get_testexecutions_report_in_range(
    test_client: TestClient, generator: DataGenerator, db_session: Session
):
    artefact = generator.gen_artefact("beta")
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build, environment, created_at=datetime.now()
    )
    generator.gen_artefact_build_environment_review(artefact_build, environment)

    response = test_client.get(
        "/v1/reports/test-executions",
        params={"start_date": (datetime.now() - timedelta(days=1)).isoformat()},
    )

    table = _read_csv_response(response)

    assert len(table) == 2
    assert table[0] == [str(c) for c in TEST_EXECUTIONS_REPORT_COLUMNS]
    assert table[1] == _expected_report_row(test_execution, db_session=db_session)


def test_get_testexecutions_report_out_range(
    test_client: TestClient, generator: DataGenerator
):
    artefact = generator.gen_artefact(
        "beta", created_at=datetime.now() - timedelta(days=2)
    )
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    generator.gen_test_execution(
        artefact_build, environment, created_at=datetime.now() - timedelta(days=2)
    )
    generator.gen_artefact_build_environment_review(artefact_build, environment)

    response = test_client.get(
        "/v1/reports/test-executions",
        params={
            "start_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "end_date": datetime.now().isoformat(),
        },
    )

    table = _read_csv_response(response)

    assert len(table) == 1
    assert table[0] == [str(c) for c in TEST_EXECUTIONS_REPORT_COLUMNS]


def test_get_testexecutions_report_overwritten_build(
    test_client: TestClient, generator: DataGenerator, db_session: Session
):
    artefact = generator.gen_artefact("beta")
    artefact_build_1 = generator.gen_artefact_build(artefact, revision=1)
    artefact_build_2 = generator.gen_artefact_build(artefact, revision=2)
    environment = generator.gen_environment()
    generator.gen_test_execution(
        artefact_build_1, environment, created_at=datetime.now()
    )
    test_execution = generator.gen_test_execution(
        artefact_build_2, environment, created_at=datetime.now()
    )
    generator.gen_artefact_build_environment_review(artefact_build_1, environment)
    generator.gen_artefact_build_environment_review(artefact_build_2, environment)

    response = test_client.get(
        "/v1/reports/test-executions",
        params={
            "start_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "end_date": datetime.now().isoformat(),
        },
    )

    table = _read_csv_response(response)

    assert len(table) == 2
    assert table[0] == [str(c) for c in TEST_EXECUTIONS_REPORT_COLUMNS]
    assert table[1] == _expected_report_row(test_execution, db_session=db_session)


def test_get_testexecutions_report_with_test_events(
    test_client: TestClient, generator: DataGenerator, db_session: Session
):
    artefact = generator.gen_artefact("beta")
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build, environment, created_at=datetime.now()
    )
    generator.gen_artefact_build_environment_review(artefact_build, environment)
    generator.gen_test_event(test_execution, "provision_fail")

    response = test_client.get(
        "/v1/reports/test-executions",
        params={
            "start_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "include_test_events": True,
        },
    )

    table = _read_csv_response(response)

    assert len(table) == 2
    assert table[0] == [
        str(column)
        for column in [
            *TEST_EXECUTIONS_REPORT_COLUMNS,
            "TestEvent.event_name",
            "TestEvent.timestamp",
            "TestEvent.detail",
        ]
    ]
    assert table[1] == _expected_report_row(
        test_execution, db_session=db_session, include_test_events=True
    )


def _read_csv_response(response: Response) -> list:
    content = response.content.decode()
    csv_reader = csv.reader(StringIO(content))
    return list(csv_reader)


def _expected_report_row(
    test_execution: TestExecution,
    db_session: Session,
    include_test_events: bool = False,
) -> list:
    environment = test_execution.environment
    artefact = test_execution.artefact_build.artefact
    family = artefact.stage.family
    environment_review = (
        db_session.query(ArtefactBuildEnvironmentReview)
        .filter(
            ArtefactBuildEnvironmentReview.artefact_build_id
            == test_execution.artefact_build_id,
            ArtefactBuildEnvironmentReview.environment_id
            == test_execution.environment_id,
        )
        .one()
    )

    expected_report = [
        family.name,
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
        "" if not test_execution.ci_link else test_execution.ci_link,
        "" if not test_execution.c3_link else test_execution.c3_link,
        "" if not test_execution.checkbox_version else test_execution.checkbox_version,
        environment.name,
        environment.architecture,
        str(environment_review.review_decision),
        environment_review.review_comment,
    ]

    if include_test_events:
        test_events = test_execution.test_events
        expected_report.extend(
            [
                str([te.event_name for te in test_events]),
                str(
                    [
                        te.timestamp.strftime("%Y-%m-%d %H:%M:%S:%f")[:-3]
                        for te in test_events
                    ]
                ),
                str([te.detail for te in test_events]),
            ]
        )

    return expected_report
