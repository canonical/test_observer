import csv
from datetime import datetime, timedelta
from io import StringIO

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi.testclient import TestClient
from httpx import Response

from test_observer.data_access.models import (
    ArtefactBuildEnvironmentReview,
    TestExecution,
)
from tests.data_generator import DataGenerator

EXPECTED_COLUMN_NAMES = [
    "Family.name",
    "Artefact.id",
    "Artefact.name",
    "Artefact.version",
    "Artefact.status",
    "Artefact.track",
    "Artefact.series",
    "Artefact.repo",
    "TestExecution.id",
    "TestExecution.status",
    "TestExecution.ci_link",
    "TestExecution.c3_link",
    "TestExecution.checkbox_version",
    "TestExecution.created_at",
    "Environment.name",
    "Environment.architecture",
    "ArtefactBuildEnvironmentReview.review_decision",
    "ArtefactBuildEnvironmentReview.review_comment",
    "TestEvents",
]


def test_get_testexecutions_report_in_range_with_test_events(
    test_client: TestClient, generator: DataGenerator, db_session: Session
):
    artefact = generator.gen_artefact("beta")
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build, environment, created_at=datetime.now()
    )
    generator.gen_artefact_build_environment_review(artefact_build, environment)
    generator.gen_test_event(test_execution, "job_start")
    generator.gen_test_event(test_execution, "provision_fail")

    response = test_client.get(
        "/v1/reports/test-executions",
        params={"start_date": (datetime.now() - timedelta(days=1)).isoformat()},
    )

    table = _read_csv_response(response)

    assert len(table) == 2
    assert table[0] == EXPECTED_COLUMN_NAMES
    assert table[1] == _expected_report_row(test_execution, db_session=db_session)


def test_get_testexecutions_report_in_range_without_test_events(
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
    assert table[0] == EXPECTED_COLUMN_NAMES
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
    assert table[0] == EXPECTED_COLUMN_NAMES


def _read_csv_response(response: Response) -> list:
    content = response.content.decode()
    csv_reader = csv.reader(StringIO(content))
    return list(csv_reader)


def _expected_report_row(
    test_execution: TestExecution,
    db_session: Session,
) -> list:
    environment = test_execution.environment
    artefact = test_execution.artefact_build.artefact
    family = artefact.stage.family
    environment_review = db_session.execute(
        select(ArtefactBuildEnvironmentReview).where(
            ArtefactBuildEnvironmentReview.artefact_build_id
            == test_execution.artefact_build_id,
            ArtefactBuildEnvironmentReview.environment_id
            == test_execution.environment_id,
        )
    ).scalar_one()

    return [
        family.name,
        str(artefact.id),
        artefact.name,
        artefact.version,
        artefact.status.name,
        artefact.track,
        artefact.series,
        artefact.repo,
        str(test_execution.id),
        test_execution.status.name,
        "" if not test_execution.ci_link else test_execution.ci_link,
        "" if not test_execution.c3_link else test_execution.c3_link,
        "" if not test_execution.checkbox_version else test_execution.checkbox_version,
        str(test_execution.created_at),
        environment.name,
        environment.architecture,
        str(environment_review.review_decision),
        environment_review.review_comment,
        str(
            [
                {
                    "event_name": test_event.event_name,
                    "timestamp": test_event.timestamp.strftime("%Y-%m-%d %H:%M:%S:%f")[
                        :-3
                    ],
                    "detail": test_event.detail,
                }
                for test_event in test_execution.test_events
            ]
        ),
    ]
