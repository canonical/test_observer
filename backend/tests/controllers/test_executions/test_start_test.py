from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from test_observer.controllers.test_executions.models import StartTestExecutionRequest
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    TestExecution,
    TestResult,
)
from test_observer.data_access.models_enums import (
    FamilyName,
    TestExecutionStatus,
)
from tests.data_generator import DataGenerator


def test_creates_all_data_models(db_session: Session, test_client: TestClient):
    response = test_client.put(
        "/v1/test-executions/start-test",
        json={
            "family": "snap",
            "name": "core22",
            "version": "abec123",
            "revision": 123,
            "track": "22",
            "store": "ubuntu",
            "arch": "arm64",
            "execution_stage": "beta",
            "environment": "cm3",
            "ci_link": "http://localhost",
        },
    )

    artefact = (
        db_session.query(Artefact)
        .filter(
            Artefact.name == "core22",
            Artefact.version == "abec123",
            Artefact.store == "ubuntu",
            Artefact.track == "22",
            Artefact.stage.has(name="beta"),
        )
        .one_or_none()
    )
    assert artefact

    environment = (
        db_session.query(Environment)
        .filter(
            Environment.name == "cm3",
            Environment.architecture == "arm64",
        )
        .one_or_none()
    )
    assert environment

    artefact_build = (
        db_session.query(ArtefactBuild)
        .filter(
            ArtefactBuild.architecture == "arm64",
            ArtefactBuild.artefact == artefact,
            ArtefactBuild.revision == 123,
        )
        .one_or_none()
    )
    assert artefact_build

    test_execution = (
        db_session.query(TestExecution)
        .filter(
            TestExecution.artefact_build == artefact_build,
            TestExecution.environment == environment,
            TestExecution.status == TestExecutionStatus.IN_PROGRESS,
        )
        .one_or_none()
    )
    assert test_execution
    assert response.json() == {"id": test_execution.id}


def test_invalid_artefact_format(test_client: TestClient):
    """Artefact with invalid format no store should not be created"""
    response = test_client.put(
        "/v1/test-executions/start-test",
        json={
            "family": "snap",
            "name": "core22",
            "version": "abec123",
            "revision": 123,
            "track": "22",
            "arch": "arm64",
            "execution_stage": "beta",
            "environment": "cm3",
            "ci_link": "http://localhost",
        },
    )
    assert response.status_code == 422


def test_uses_existing_models(
    db_session: Session,
    test_client: TestClient,
    generator: DataGenerator,
):
    artefact = generator.gen_artefact("beta")
    environment = generator.gen_environment()
    artefact_build = generator.gen_artefact_build(artefact)
    test_execution = generator.gen_test_execution(
        artefact_build,
        environment,
        ci_link="http://should-be-changed",
        c3_link="http://should-be-nulled",
    )
    test_case = generator.gen_test_case()
    generator.gen_test_result(test_case, test_execution)

    request = StartTestExecutionRequest(
        family=FamilyName(artefact.stage.family.name),
        name=artefact.name,
        version=artefact.version,
        revision=artefact_build.revision,
        track=artefact.track,
        store=artefact.store,
        arch=artefact_build.architecture,
        execution_stage=artefact.stage.name,
        environment=environment.name,
        ci_link="http://localhost/",
    )

    test_execution_id = test_client.put(
        "/v1/test-executions/start-test",
        json=request.model_dump(mode="json"),
    ).json()["id"]

    test_execution = (
        db_session.query(TestExecution)
        .where(TestExecution.id == test_execution_id)
        .one()
    )

    assert test_execution.artefact_build_id == artefact_build.id
    assert test_execution.environment_id == environment.id
    assert test_execution.status == TestExecutionStatus.IN_PROGRESS
    assert test_execution.ci_link == "http://localhost/"
    assert test_execution.c3_link is None
    # deleted existing test results
    assert (
        db_session.query(TestResult)
        .filter(TestResult.test_case_id == test_case.id)
        .one_or_none()
        is None
    )


def test_new_artefacts_get_assigned_a_reviewer(
    db_session: Session, test_client: TestClient, generator: DataGenerator
):
    user = generator.gen_user()

    test_client.put(
        "/v1/test-executions/start-test",
        json={
            "family": "snap",
            "name": "core22",
            "version": "abec123",
            "revision": 123,
            "track": "22",
            "store": "ubuntu",
            "arch": "arm64",
            "execution_stage": "beta",
            "environment": "cm3",
            "ci_link": "http://localhost",
        },
    )

    artefact = db_session.query(Artefact).filter(Artefact.name == "core22").one()
    assert artefact.assignee is not None
    assert artefact.assignee.launchpad_handle == user.launchpad_handle
