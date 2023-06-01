from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.data_access.models import Artefact, ArtefactBuild, Environment, TestExecution

from src.data_access.models_enums import TestExecutionStatus


def test_creates_all_data_models(db_session: Session, test_client: TestClient):
    test_client.put(
        "/v1/test-execution/start",
        json={
            "family": "snap",
            "name": "core22",
            "version": "abec123",
            "revision": 123,
            "source": {"track": "22"},
            "arch": "arm64",
            "execution_stage": "beta",
            "environment": "cm3",
        },
    )

    artefact = (
        db_session.query(Artefact)
        .filter(
            Artefact.name == "core22",
            Artefact.version == "abec123",
            Artefact.source == {"track": "22"},
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

    assert (
        db_session.query(TestExecution)
        .filter(
            TestExecution.artefact_build == artefact_build,
            TestExecution.environment == environment,
            TestExecution.status == TestExecutionStatus.IN_PROGRESS,
        )
        .one_or_none()
    )
