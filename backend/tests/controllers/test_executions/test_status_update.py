import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from test_observer.data_access.models_enums import StageName, TestExecutionStatus
from tests.data_generator import DataGenerator


def test_status_updates_stored(test_client: TestClient, generator: DataGenerator):
    artefact = generator.gen_artefact(StageName.beta)
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build, environment, ci_link="http://localhost"
    )

    response = test_client.put(
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
        artefact_build, environment, ci_link="http://localhost"
    )

    for _ in range(3):
        test_client.put(
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
        )

    db_session.refresh(test_execution)
    assert len(test_execution.test_events) == 2


def test_get_status_update(test_client: TestClient, generator: DataGenerator):
    artefact = generator.gen_artefact(StageName.beta)
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build, environment, ci_link="http://localhost"
    )

    test_client.put(
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
    )
    get_response = test_client.get(
        f"/v1/test-executions/{test_execution.id}/status_update"
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
        artefact_build, environment, ci_link="http://localhost"
    )

    response = test_client.put(
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
    )
    assert response.status_code == 422


def test_status_update_normal_exit(test_client: TestClient, generator: DataGenerator):
    artefact = generator.gen_artefact(StageName.beta)
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build, environment, ci_link="http://localhost"
    )

    test_client.put(
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
    )
    assert test_execution.status == TestExecutionStatus.ENDED_PREMATURELY
