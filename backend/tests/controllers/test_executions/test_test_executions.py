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


import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from test_observer.controllers.test_executions.models import StartTestExecutionRequest
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    Stage,
    TestCase,
    TestExecution,
    TestResult,
)
from test_observer.data_access.models_enums import (
    FamilyName,
    TestExecutionReviewDecision,
    TestExecutionStatus,
    TestResultStatus,
)
from tests.data_generator import DataGenerator


@pytest.fixture
def test_execution(db_session: Session) -> TestExecution:
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
    test_case = TestCase(name="some-test", category="")
    test_result = TestResult(
        test_case=test_case,
        test_execution=test_execution,
        status=TestResultStatus.PASSED,
        comment="",
        io_log="",
    )

    db_session.add_all(
        [
            artefact,
            environment,
            artefact_build,
            test_execution,
            test_case,
            test_result,
        ]
    )
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
    assert (
        db_session.query(TestResult)
        .filter(TestResult.test_case_id == test_case.id)
        .one_or_none()
        is None
    )


def test_report_test_execution_data(
    db_session: Session, test_client: TestClient, generator: DataGenerator
):
    ci_link = "http://localhost"
    c3_link = "http://c3.localhost"
    artefact = generator.gen_artefact(stage_name="beta")
    artefact_build = ArtefactBuild(architecture="some arch", artefact=artefact)
    environment = Environment(name="some environment", architecture="some arch")
    test_execution = TestExecution(
        environment=environment, artefact_build=artefact_build, ci_link=ci_link
    )
    test_case = TestCase(name="test-name-1", category="")
    db_session.add_all([artefact_build, environment, test_execution, test_case])
    db_session.commit()

    response = test_client.put(
        "/v1/test-executions/end-test",
        json={
            "id": 1,
            "ci_link": ci_link,
            "c3_link": c3_link,
            "test_results": [
                {
                    "id": 1,
                    "name": test_case.name,
                    "status": "pass",
                    "category": test_case.category,
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
    assert test_execution.c3_link == c3_link
    assert test_execution.test_results[0].test_case.name == "test-name-1"
    assert test_execution.test_results[0].status == TestResultStatus.PASSED
    assert test_execution.test_results[1].test_case.name == "test-name-2"
    assert test_execution.test_results[1].status == TestResultStatus.SKIPPED


def test_end_test_is_idempotent(
    db_session: Session, test_client: TestClient, generator: DataGenerator
):
    ci_link = "http://localhost"
    artefact = generator.gen_artefact(stage_name="beta")
    artefact_build = ArtefactBuild(architecture="some arch", artefact=artefact)
    environment = Environment(name="some environment", architecture="some arch")
    test_execution = TestExecution(
        environment=environment, artefact_build=artefact_build, ci_link=ci_link
    )
    test_case = TestCase(name="test-name-1", category="")
    db_session.add_all([artefact_build, environment, test_execution, test_case])
    db_session.commit()

    for _ in range(2):
        test_client.put(
            "/v1/test-executions/end-test",
            json={
                "id": 1,
                "ci_link": ci_link,
                "test_results": [
                    {
                        "id": 1,
                        "name": test_case.name,
                        "status": "pass",
                        "category": test_case.category,
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

    assert len(test_execution.test_results) == 2


def test_updates_test_execution(
    db_session: Session, test_client: TestClient, test_execution: TestExecution
):
    new_review_decision = [
        TestExecutionReviewDecision.APPROVED_FAULTY_HARDWARE.name,
        TestExecutionReviewDecision.APPROVED_INCONSISTENT_TEST.name,
    ]
    test_client.patch(
        f"/v1/test-executions/{test_execution.id}",
        json={
            "ci_link": "http://ci_link/",
            "c3_link": "http://c3_link/",
            "status": TestExecutionStatus.PASSED.name,
            "review_decision": new_review_decision,
            "review_comment": "Tests fail because of broken keyboard",
        },
    )
    db_session.refresh(test_execution)
    assert test_execution.ci_link == "http://ci_link/"
    assert test_execution.c3_link == "http://c3_link/"
    assert test_execution.status == TestExecutionStatus.PASSED
    assert set(test_execution.review_decision) == set(new_review_decision)
    assert test_execution.review_comment == "Tests fail because of broken keyboard"


def test_review_test_execution_fails_if_both_failed_and_approved(
    db_session: Session, test_client: TestClient, test_execution: TestExecution
):
    response = test_client.patch(
        f"/v1/test-executions/{test_execution.id}",
        json={
            "review_decision": [
                TestExecutionReviewDecision.REJECTED.name,
                TestExecutionReviewDecision.APPROVED_INCONSISTENT_TEST.name,
            ],
        },
    )

    db_session.refresh(test_execution)
    assert response.status_code == 422


def test_fetch_test_results(
    db_session: Session, test_client: TestClient, generator: DataGenerator
):
    artefact_first = generator.gen_artefact(stage_name="beta", version="1.1.1")
    artefact_build_first = ArtefactBuild(
        architecture="some arch", artefact=artefact_first
    )
    environment = Environment(name="some environment", architecture="some arch")
    test_execution_first = TestExecution(
        environment=environment,
        artefact_build=artefact_build_first,
        ci_link="http://cilink1",
        status=TestExecutionStatus.PASSED,
    )
    test_case = TestCase(name="test-name-1", category="")
    test_result_first = TestResult(
        test_case=test_case,
        test_execution=test_execution_first,
        status=TestResultStatus.FAILED,
        comment="",
        io_log="",
    )
    db_session.add_all(
        [
            artefact_build_first,
            environment,
            test_execution_first,
            test_case,
            test_result_first,
        ]
    )
    db_session.commit()

    artefact_second = generator.gen_artefact(stage_name="beta", version="1.1.2")
    artefact_build_second = ArtefactBuild(
        architecture="some arch", artefact=artefact_second
    )
    test_execution_second = TestExecution(
        environment=environment,
        artefact_build=artefact_build_second,
        ci_link="http://cilink2",
        status=TestExecutionStatus.PASSED,
    )
    test_result_second = TestResult(
        test_case=test_case,
        test_execution=test_execution_second,
        status=TestResultStatus.PASSED,
        comment="",
        io_log="",
    )
    db_session.add_all(
        [artefact_build_second, test_execution_second, test_result_second]
    )
    db_session.commit()

    response = test_client.get(
        f"/v1/test-executions/{test_execution_second.id}/test-results"
    )

    assert response.status_code == 200
    json = response.json()
    assert json[0]["name"] == test_case.name
    assert json[0]["category"] == test_case.category
    assert json[0]["status"] == test_result_second.status.name
    assert json[0]["comment"] == test_result_second.comment
    assert json[0]["io_log"] == test_result_second.io_log
    assert json[0]["previous_results"] == [
        {
            "status": test_result_first.status,
            "version": artefact_first.version,
        }
    ]


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
