# Copyright (C) 2023 Canonical Ltd.
#
# This file is part of Test Observer Backend.
#
# Test Observer Backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# Test Observer Backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import csv
from datetime import datetime, timedelta
from io import StringIO

from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.common.permissions import Permission
from test_observer.data_access.models import (
    ArtefactBuildEnvironmentReview,
    TestExecution,
)
from test_observer.data_access.models_enums import StageName
from tests.data_generator import DataGenerator
from tests.conftest import make_authenticated_request

EXPECTED_COLUMN_NAMES = [
    "Artefact.family",
    "Artefact.id",
    "Artefact.name",
    "Artefact.version",
    "Artefact.status",
    "Artefact.track",
    "Artefact.stage",
    "Artefact.series",
    "Artefact.repo",
    "Artefact.os",
    "TestExecution.id",
    "TestExecution.status",
    "TestExecution.ci_link",
    "TestExecution.c3_link",
    "TestExecution.checkbox_version",
    "TestExecution.test_plan",
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
    artefact = generator.gen_artefact(StageName.beta)
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build, environment, created_at=datetime.now()
    )
    generator.gen_artefact_build_environment_review(artefact_build, environment)
    generator.gen_test_event(test_execution, "job_start")
    generator.gen_test_event(test_execution, "provision_fail")

    response = make_authenticated_request(
        lambda: test_client.get(
            "/v1/reports/test-executions",
            params={"start_date": (datetime.now() - timedelta(days=1)).isoformat()},
        ),
        Permission.view_report,
    )

    table = _read_csv_response(response)

    assert len(table) == 2
    assert table[0] == EXPECTED_COLUMN_NAMES
    assert table[1] == _expected_report_row(test_execution, db_session=db_session)


def test_get_testexecutions_report_in_range_without_test_events(
    test_client: TestClient, generator: DataGenerator, db_session: Session
):
    artefact = generator.gen_artefact(StageName.beta)
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build, environment, created_at=datetime.now()
    )
    generator.gen_artefact_build_environment_review(artefact_build, environment)

    response = make_authenticated_request(
        lambda: test_client.get(
            "/v1/reports/test-executions",
            params={"start_date": (datetime.now() - timedelta(days=1)).isoformat()},
        ),
        Permission.view_report,
    )

    table = _read_csv_response(response)

    assert len(table) == 2
    assert table[0] == EXPECTED_COLUMN_NAMES
    assert table[1] == _expected_report_row(test_execution, db_session=db_session)


def test_get_testexecutions_report_out_range(
    test_client: TestClient, generator: DataGenerator
):
    artefact = generator.gen_artefact(
        StageName.beta, created_at=datetime.now() - timedelta(days=2)
    )
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    generator.gen_test_execution(
        artefact_build, environment, created_at=datetime.now() - timedelta(days=2)
    )
    generator.gen_artefact_build_environment_review(artefact_build, environment)

    response = make_authenticated_request(
        lambda: test_client.get(
            "/v1/reports/test-executions",
            params={
                "start_date": (datetime.now() - timedelta(days=1)).isoformat(),
                "end_date": datetime.now().isoformat(),
            },
        ),
        Permission.view_report,
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
    environment_review = db_session.execute(
        select(ArtefactBuildEnvironmentReview).where(
            ArtefactBuildEnvironmentReview.artefact_build_id
            == test_execution.artefact_build_id,
            ArtefactBuildEnvironmentReview.environment_id
            == test_execution.environment_id,
        )
    ).scalar_one()

    return [
        artefact.family,
        str(artefact.id),
        artefact.name,
        artefact.version,
        artefact.status.name,
        artefact.track,
        artefact.stage,
        artefact.series,
        artefact.repo,
        artefact.os,
        str(test_execution.id),
        test_execution.status.name,
        "" if not test_execution.ci_link else test_execution.ci_link,
        "" if not test_execution.c3_link else test_execution.c3_link,
        "" if not test_execution.checkbox_version else test_execution.checkbox_version,
        test_execution.test_plan.name,
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
