from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from test_observer.data_access.models import (
    Artefact,
    Stage,
    TestExecution,
    ArtefactBuild,
    Environment,
)
from test_observer.data_access.models_enums import TestExecutionStatus


def test_updates_test_execution(db_session: Session, test_client: TestClient):
    stage = db_session.query(Stage).filter(Stage.name == "beta").one()
    artefact = Artefact(name="some artefact", version="1.0.0", source={}, stage=stage)
    artefact_build = ArtefactBuild(architecture="some arch", artefact=artefact)
    environment = Environment(name="some environment", architecture="some arch")
    test_execution = TestExecution(
        environment=environment, artefact_build=artefact_build
    )
    db_session.add_all([artefact, artefact_build, environment, test_execution])
    db_session.commit()
    db_session.refresh(test_execution)

    test_client.patch(
        f"/v1/test-executions/{test_execution.id}",
        json={
            "jenkins_link": "some jenkins link",
            "c3_link": "some c3 link",
            "status": TestExecutionStatus.PASSED.name,
        },
    )

    db_session.refresh(test_execution)
    assert test_execution.jenkins_link == "some jenkins link"
    assert test_execution.c3_link == "some c3 link"
    assert test_execution.status == TestExecutionStatus.PASSED
