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


import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from test_observer.common.permissions import Permission
from test_observer.data_access.models_enums import StageName, TestExecutionStatus

from tests.data_generator import DataGenerator
from tests.conftest import make_authenticated_request


def test_status_updates_stored(test_client: TestClient, generator: DataGenerator):
    artefact = generator.gen_artefact(StageName.beta)
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build,
        environment,
        ci_link="http://localhost",
        relevant_links=[{"label": "Doc Link", "url": "http://example.com/doc"}],
    )

    response = make_authenticated_request(
        lambda: test_client.put(
            f"/v1/test-executions/{test_execution.id}/status_update",
            json={
                "agent_id": "test_agent",
                "job_queue": "test_job_queue",
                "events": [
                    {
                        "event_name": "started_setup",
                        "timestamp": "2015-03-21T11:08:14.859831",
                        "detail": "my_detail_one",
                    },
                    {
                        "event_name": "ended_setup",
                        "timestamp": "2015-03-21T11:08:15.859831",
                        "detail": "my_detail_two",
                    },
                    {
                        "event_name": "job_end",
                        "timestamp": "2015-03-21T11:08:15.859831",
                        "detail": "my_detail_three",
                    },
                ],
            },
        ),
        Permission.change_test,
    )
    assert response.status_code == 200
    assert test_execution.test_events[0].event_name == "started_setup"
    assert test_execution.test_events[0].timestamp == datetime.datetime.fromisoformat(
        "2015-03-21T11:08:14.859831"
    )
    assert test_execution.test_events[0].detail == "my_detail_one"
    assert test_execution.test_events[1].event_name == "ended_setup"
    assert test_execution.test_events[1].timestamp == datetime.datetime.fromisoformat(
        "2015-03-21T11:08:15.859831"
    )
    assert test_execution.test_events[1].detail == "my_detail_two"
    assert test_execution.status == "ENDED_PREMATURELY"


def test_status_updates_is_idempotent(
    test_client: TestClient, generator: DataGenerator, db_session: Session
):
    artefact = generator.gen_artefact(StageName.beta)
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build,
        environment,
        ci_link="http://localhost",
        relevant_links=[
            {"label": "Support Ticket", "url": "http://example.com/ticket/456"}
        ],
    )

    for _ in range(3):
        make_authenticated_request(
            lambda: test_client.put(
                f"/v1/test-executions/{test_execution.id}/status_update",
                json={
                    "agent_id": "test_agent",
                    "job_queue": "test_job_queue",
                    "events": [
                        {
                            "event_name": "started_setup",
                            "timestamp": "2015-03-21T11:08:14.859831",
                            "detail": "my_detail_one",
                        },
                        {
                            "event_name": "ended_setup",
                            "timestamp": "2015-03-21T11:08:15.859831",
                            "detail": "my_detail_two",
                        },
                    ],
                },
            ),
            Permission.change_test,
        )

    db_session.refresh(test_execution)
    assert len(test_execution.test_events) == 2


def test_get_status_update(test_client: TestClient, generator: DataGenerator):
    artefact = generator.gen_artefact(StageName.beta)
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build,
        environment,
        ci_link="http://localhost",
        relevant_links=[
            {"label": "Release Notes", "url": "http://example.com/release"}
        ],
    )

    make_authenticated_request(
        lambda: test_client.put(
            f"/v1/test-executions/{test_execution.id}/status_update",
            json={
                "agent_id": "test_agent",
                "job_queue": "test_job_queue",
                "events": [
                    {
                        "event_name": "started_setup",
                        "timestamp": "2015-03-21T11:08:14.859831",
                        "detail": "my_detail_one",
                    },
                    {
                        "event_name": "ended_setup",
                        "timestamp": "2015-03-21T11:08:15.859831",
                        "detail": "my_detail_two",
                    },
                    {
                        "event_name": "job_end",
                        "timestamp": "2015-03-21T11:08:15.859831",
                        "detail": "my_detail_three",
                    },
                ],
            },
        ),
        Permission.change_test,
    )
    get_response = make_authenticated_request(
        lambda: test_client.get(
            f"/v1/test-executions/{test_execution.id}/status_update"
        ),
        Permission.view_test,
    )

    assert get_response.status_code == 200
    json = get_response.json()
    assert json[0]["event_name"] == "started_setup"
    assert json[0]["timestamp"] == "2015-03-21T11:08:14.859831"
    assert json[0]["detail"] == "my_detail_one"
    assert json[1]["event_name"] == "ended_setup"
    assert json[1]["timestamp"] == "2015-03-21T11:08:15.859831"
    assert json[1]["detail"] == "my_detail_two"


def test_status_updates_invalid_timestamp(
    test_client: TestClient, generator: DataGenerator
):
    artefact = generator.gen_artefact(StageName.beta)
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build,
        environment,
        ci_link="http://localhost",
        relevant_links=[{"label": "External Info", "url": "http://example.com/info"}],
    )

    response = make_authenticated_request(
        lambda: test_client.put(
            f"/v1/test-executions/{test_execution.id}/status_update",
            json={
                "agent_id": "test_agent",
                "job_queue": "test_job_queue",
                "events": [
                    {
                        "event_name": "started_setup",
                        "timestamp": "201-03-21T11:08:14.859831",
                        "detail": "my_detail_one",
                    },
                    {
                        "event_name": "ended_setup",
                        "timestamp": "20-03-21T11:08:15.859831",
                        "detail": "my_detail_two",
                    },
                ],
            },
        ),
        Permission.change_test,
    )
    assert response.status_code == 422


def test_status_update_normal_exit(test_client: TestClient, generator: DataGenerator):
    artefact = generator.gen_artefact(StageName.beta)
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build,
        environment,
        ci_link="http://localhost",
        relevant_links=[{"label": "Logs", "url": "http://example.com/logs"}],
    )

    make_authenticated_request(
        lambda: test_client.put(
            f"/v1/test-executions/{test_execution.id}/status_update",
            json={
                "agent_id": "test_agent",
                "job_queue": "test_job_queue",
                "events": [
                    {
                        "event_name": "started_setup",
                        "timestamp": "2015-03-21T11:08:14.859831",
                        "detail": "my_detail_one",
                    },
                    {
                        "event_name": "ended_setup",
                        "timestamp": "2015-03-21T11:08:15.859831",
                        "detail": "my_detail_two",
                    },
                    {
                        "event_name": "job_end",
                        "timestamp": "2015-03-21T11:08:16.859831",
                        "detail": "normal_exit",
                    },
                ],
            },
        ),
        Permission.change_test,
    )
    assert test_execution.status == TestExecutionStatus.ENDED_PREMATURELY


def test_post_status_update_appends_events(
    test_client: TestClient, generator: DataGenerator, db_session: Session
):
    artefact = generator.gen_artefact(StageName.beta)
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build,
        environment,
        ci_link="http://localhost",
        relevant_links=[{"label": "CI", "url": "http://example.com/ci"}],
    )

    response1 = make_authenticated_request(
        lambda: test_client.post(
            f"/v1/test-executions/{test_execution.id}/status_update",
            json={
                "events": [
                    {
                        "event_name": "started_setup",
                        "timestamp": "2025-06-21T10:00:00.000000",
                        "detail": "Initial setup started",
                    }
                ]
            },
        ),
        Permission.change_test,
    )
    assert response1.status_code == 200

    response2 = make_authenticated_request(
        lambda: test_client.post(
            f"/v1/test-executions/{test_execution.id}/status_update",
            json={
                "events": [
                    {
                        "event_name": "ended_setup",
                        "timestamp": "2025-06-21T10:05:00.000000",
                        "detail": "Setup completed",
                    }
                ]
            },
        ),
        Permission.change_test,
    )
    assert response2.status_code == 200

    db_session.refresh(test_execution)
    assert len(test_execution.test_events) == 2
    assert test_execution.test_events[0].event_name == "started_setup"
    assert test_execution.test_events[1].event_name == "ended_setup"
