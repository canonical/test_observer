from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from test_observer.data_access.models import Environment, TestExecution

from tests.helpers import create_artefact, create_artefact_builds


def test_get_artefact(db_session: Session, test_client: TestClient):
    artefact = create_artefact(db_session, "beta")
    artefact_build = create_artefact_builds(db_session, artefact, 1)[0]
    environment = Environment(
        name="some-environment", architecture=artefact_build.architecture
    )
    test_execution = TestExecution(
        artefact_build=artefact_build, environment=environment
    )
    db_session.add_all([environment, test_execution])
    db_session.commit()

    response = test_client.get(f"/v1/artefacts/{artefact.id}/builds")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": artefact_build.id,
            "revision": artefact_build.revision,
            "test_executions": [
                {
                    "id": test_execution.id,
                    "jenkins_link": test_execution.jenkins_link,
                    "c3_link": test_execution.c3_link,
                    "environment": {
                        "id": environment.id,
                        "name": environment.name,
                        "architecture": environment.architecture,
                    },
                }
            ],
        }
    ]
