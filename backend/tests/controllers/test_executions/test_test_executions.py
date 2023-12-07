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
from test_observer.data_access.models_enums import (
    FamilyName,
    TestExecutionReviewStatus,
    TestExecutionStatus,
)
from tests.helpers import create_artefact


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
        ci_link="http://localhost/",
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
    test_execution = TestExecution(
        environment=environment,
        artefact_build=artefact_build,
        ci_link="http://should-be-changed",
        c3_link="http://should-be-nulled",
    )

    db_session.add_all([artefact, environment, artefact_build, test_execution])
    db_session.commit()

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


def test_report_test_execution_data(db_session: Session, test_client: TestClient):
    ci_link = "http://localhost"
    artefact = create_artefact(db_session, stage_name="beta")
    artefact_build = ArtefactBuild(architecture="some arch", artefact=artefact)
    environment = Environment(name="some environment", architecture="some arch")
    test_execution = TestExecution(
        environment=environment, artefact_build=artefact_build, ci_link=ci_link
    )
    db_session.add_all([artefact_build, environment, test_execution])
    db_session.commit()

    response = test_client.put(
        "/v1/test-executions/end-test",
        json={
            "id": 1,
            "ci_link": ci_link,
            "test_results": [
                {
                    "id": 1,
                    "name": "test-name-1",
                    "status": "pass",
                    "category": "",
                    "comment": "",
                    "io_log": "",
                },
                {
                    "id": 2,
                    "name": "test-name-2",
                    "status": "skip",
                    "category": "",
                    "comment": "",
                    "io_log": "",
                },
            ],
        },
    )

    assert response.status_code == 200
    assert test_execution.status == TestExecutionStatus.PASSED


def _prepare_test_execution_object(db_session: Session) -> TestExecution:
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

    return test_execution


def test_updates_test_execution(db_session: Session, test_client: TestClient):
    test_execution: TestExecution = _prepare_test_execution_object(db_session)

    test_client.patch(
        f"/v1/test-executions/{test_execution.id}",
        json={
            "ci_link": "http://ci_link/",
            "c3_link": "http://c3_link/",
            "status": TestExecutionStatus.PASSED.name,
        },
    )

    db_session.refresh(test_execution)
    assert test_execution.ci_link == "http://ci_link/"
    assert test_execution.c3_link == "http://c3_link/"
    assert test_execution.status == TestExecutionStatus.PASSED


def test_review_test_execution(db_session: Session, test_client: TestClient):
    test_execution: TestExecution = _prepare_test_execution_object(db_session)

    test_client.patch(
        f"/v1/test-executions/{test_execution.id}/review",
        json={
            "review_status": [
                TestExecutionReviewStatus.APPROVED_UNSTABLE_PHSYICAL_INFRA.name,
                TestExecutionReviewStatus.APPROVED_FAULTY_HARDWARE.name,
            ],
            "review_comment": "Known issue with our infrastructure",
        },
    )

    db_session.refresh(test_execution)
    assert test_execution.review_comment == "Known issue with our infrastructure"
    assert test_execution.review_status == [
        TestExecutionReviewStatus.APPROVED_UNSTABLE_PHSYICAL_INFRA.name,
        TestExecutionReviewStatus.APPROVED_FAULTY_HARDWARE.name,
    ]


def _execute_review_test_execution_invalid_input(
    db_session: Session,
    test_client: TestClient,
    review_status: list[str],
) -> None:
    test_execution: TestExecution = _prepare_test_execution_object(db_session)

    response = test_client.patch(
        f"/v1/test-executions/{test_execution.id}/review",
        json={
            "review_status": review_status,
        },
    )

    db_session.refresh(test_execution)
    assert response.status_code == 422


def test_review_test_execution_fails_if_both_failed_and_approved(
    db_session: Session, test_client: TestClient
):
    _execute_review_test_execution_invalid_input(
        db_session=db_session,
        test_client=test_client,
        review_status=[
            TestExecutionReviewStatus.MARKED_AS_FAILED.name,
            TestExecutionReviewStatus.APPROVED_GENERIC.name,
        ],
    )


def test_review_test_execution_fails_if_both_undecided_and_failed(
    db_session: Session, test_client: TestClient
):
    _execute_review_test_execution_invalid_input(
        db_session=db_session,
        test_client=test_client,
        review_status=[
            TestExecutionReviewStatus.MARKED_AS_FAILED.name,
            TestExecutionReviewStatus.UNDECIDED.name,
        ],
    )


def test_review_test_execution_fails_if_both_undecided_and_approved(
    db_session: Session, test_client: TestClient
):
    _execute_review_test_execution_invalid_input(
        db_session=db_session,
        test_client=test_client,
        review_status=[
            TestExecutionReviewStatus.APPROVED_GENERIC.name,
            TestExecutionReviewStatus.UNDECIDED.name,
        ],
    )
