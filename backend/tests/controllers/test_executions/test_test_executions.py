# Copyright 2023 Canonical Ltd.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Written by:
#        Omar Selo <omar.selo@canonical.com>
#        Nadzeya Hutsko <nadzeya.hutsko@canonical.com>


from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from test_observer.controllers.test_executions.models import StartTestExecutionRequest
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    Stage,
    TestExecution,
)
from test_observer.data_access.models_enums import FamilyName, TestExecutionStatus


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
        },
    )
    assert response.status_code == 422


def test_uses_existing_models(db_session: Session, test_client: TestClient):
    request = StartTestExecutionRequest(
        family=FamilyName.SNAP,
        name="core22",
        version="abec123",
        revision=123,
        track="22",
        store="ubuntu",
        arch="arm64",
        execution_stage="beta",
        environment="cm3",
    )
    stage = (
        db_session.query(Stage).filter(Stage.name == request.execution_stage).first()
    )
    artefact = Artefact(
        name=request.name,
        version=request.version,
        track=request.track,
        store=request.store,
        stage=stage,
    )
    environment = Environment(
        name=request.environment,
        architecture=request.arch,
    )
    artefact_build = ArtefactBuild(
        architecture=request.arch,
        revision=request.revision,
        artefact=artefact,
    )

    db_session.add_all([artefact, environment, artefact_build])
    db_session.commit()

    test_execution_id = test_client.put(
        "/v1/test-executions/start-test",
        json=request.model_dump(),
    ).json()["id"]

    test_execution = (
        db_session.query(TestExecution)
        .where(TestExecution.id == test_execution_id)
        .one()
    )

    assert test_execution.artefact_build_id == artefact_build.id
    assert test_execution.environment_id == environment.id
    assert test_execution.status == TestExecutionStatus.IN_PROGRESS


def test_updates_test_execution(db_session: Session, test_client: TestClient):
    stage = db_session.query(Stage).filter(Stage.name == "beta").one()
    artefact = Artefact(name="some artefact", version="1.0.0", stage=stage)
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
