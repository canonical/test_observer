# Copyright 2024 Canonical Ltd.
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

from collections.abc import Callable
from datetime import date, timedelta
from typing import Any, TypeAlias

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy.orm import Session

from test_observer.controllers.test_executions.models import StartTestExecutionRequest
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    ArtefactBuildEnvironmentReview,
    Environment,
    TestExecution,
    TestResult,
)
from test_observer.data_access.models_enums import FamilyName, TestExecutionStatus
from tests.data_generator import DataGenerator

Execute: TypeAlias = Callable[[dict[str, Any]], Response]


@pytest.fixture
def execute(test_client: TestClient) -> Execute:
    def execute_helper(data: dict[str, Any]) -> Response:
        return test_client.put("/v1/test-executions/start-test", json=data)

    return execute_helper


def test_creates_all_data_models(db_session: Session, execute: Execute):
    response = execute(
        {
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
        }
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

    environment_review = (
        db_session.query(ArtefactBuildEnvironmentReview)
        .filter(
            ArtefactBuildEnvironmentReview.artefact_build_id == artefact_build.id,
            ArtefactBuildEnvironmentReview.environment_id == environment.id,
        )
        .one_or_none()
    )
    assert environment_review

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


def test_invalid_artefact_format(execute: Execute):
    """Artefact with invalid format no store should not be created"""
    response = execute(
        {
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
    execute: Execute,
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

    test_execution_id = execute(
        request.model_dump(mode="json"),
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
    db_session: Session, execute: Execute, generator: DataGenerator
):
    user = generator.gen_user()

    execute(
        {
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


def test_non_kernel_artefact_due_date(db_session: Session, execute: Execute):
    """
    For non-kernel snaps, the default due date should be set to now + 10 days
    """
    execute(
        {
            "family": FamilyName.SNAP,
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

    assert artefact is not None
    assert artefact.due_date == date.today() + timedelta(10)


def test_kernel_artefact_due_date(db_session: Session, execute: Execute):
    """
    For kernel artefacts, due date shouldn't be set to default
    """
    execute(
        {
            "family": FamilyName.SNAP,
            "name": "pi-kernel",
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
            Artefact.name == "pi-kernel",
            Artefact.version == "abec123",
            Artefact.store == "ubuntu",
            Artefact.track == "22",
            Artefact.stage.has(name="beta"),
        )
        .one_or_none()
    )

    assert artefact is not None
    assert artefact.due_date is None


def test_deletes_rerun_request_if_different_ci_link(
    execute: Execute, generator: DataGenerator, db_session: Session
):
    a = generator.gen_artefact("beta")
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment()
    te = generator.gen_test_execution(ab, e, ci_link="ci.link")
    generator.gen_rerun_request(te)

    assert te.rerun_request

    execute(
        {
            "family": a.stage.family.name,
            "name": a.name,
            "version": a.version,
            "revision": ab.revision,
            "track": a.track,
            "store": a.store,
            "arch": ab.architecture,
            "execution_stage": a.stage.name,
            "environment": e.name,
            "ci_link": "different-ci.link",
        },
    )

    db_session.refresh(te)
    assert not te.rerun_request


def test_keep_rerun_request_if_same_ci_link(execute: Execute, generator: DataGenerator):
    a = generator.gen_artefact("beta")
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment()
    te = generator.gen_test_execution(ab, e, ci_link="ci.link")
    generator.gen_rerun_request(te)

    assert te.rerun_request

    execute(
        {
            "family": a.stage.family.name,
            "name": a.name,
            "version": a.version,
            "revision": ab.revision,
            "track": a.track,
            "store": a.store,
            "arch": ab.architecture,
            "execution_stage": a.stage.name,
            "environment": e.name,
            "ci_link": "ci.link",
        },
    )

    assert te.rerun_request
