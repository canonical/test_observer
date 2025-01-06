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

from test_observer.controllers.test_executions.models import (
    StartSnapTestExecutionRequest,
)
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    ArtefactBuildEnvironmentReview,
    Environment,
    TestExecution,
)
from test_observer.data_access.models_enums import FamilyName, TestExecutionStatus
from tests.asserts import assert_fails_validation
from tests.data_generator import DataGenerator

Execute: TypeAlias = Callable[[dict[str, Any]], Response]


snap_test_request = {
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
    "test_plan": "test plan",
}

deb_test_request = {
    "family": "deb",
    "name": "linux-generic-hwe-22.04",
    "version": "6.8.0-50.51~22.04.1",
    "series": "jammy",
    "repo": "main",
    "execution_stage": "proposed",
    "arch": "amd64",
    "environment": "xps",
    "ci_link": "http://localhost",
    "test_plan": "test plan",
}


@pytest.fixture
def execute(test_client: TestClient) -> Execute:
    def execute_helper(data: dict[str, Any]) -> Response:
        return test_client.put("/v1/test-executions/start-test", json=data)

    return execute_helper


def test_requires_family_field(execute: Execute):
    request = snap_test_request.copy()
    request.pop("family")
    response = execute(request)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "field",
    [
        "name",
        "version",
        "revision",
        "arch",
        "execution_stage",
        "environment",
        "ci_link",
        "test_plan",
        "store",
        "track",
    ],
)
def test_snap_required_fields(execute: Execute, field: str):
    request = snap_test_request.copy()
    request.pop(field)
    response = execute(request)

    assert_fails_validation(response, field, "missing")


@pytest.mark.parametrize(
    "field",
    [
        "name",
        "version",
        "series",
        "repo",
        "arch",
        "execution_stage",
        "environment",
        "ci_link",
        "test_plan",
    ],
)
def test_deb_required_fields(execute: Execute, field: str):
    request = deb_test_request.copy()
    request.pop(field)
    response = execute(request)

    assert_fails_validation(response, field, "missing")


def test_creates_all_data_models(db_session: Session, execute: Execute):
    response = execute(snap_test_request)

    artefact = (
        db_session.query(Artefact)
        .filter(
            Artefact.name == snap_test_request["name"],
            Artefact.version == snap_test_request["version"],
            Artefact.store == snap_test_request["store"],
            Artefact.track == snap_test_request["track"],
            Artefact.stage.has(name=snap_test_request["execution_stage"]),
        )
        .one_or_none()
    )
    assert artefact

    environment = (
        db_session.query(Environment)
        .filter(
            Environment.name == snap_test_request["environment"],
            Environment.architecture == snap_test_request["arch"],
        )
        .one_or_none()
    )
    assert environment

    artefact_build = (
        db_session.query(ArtefactBuild)
        .filter(
            ArtefactBuild.architecture == snap_test_request["arch"],
            ArtefactBuild.artefact == artefact,
            ArtefactBuild.revision == snap_test_request["revision"],
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
            TestExecution.test_plan == snap_test_request["test_plan"],
        )
        .one_or_none()
    )
    assert test_execution
    assert response.json() == {"id": test_execution.id}


def test_uses_existing_models(
    db_session: Session,
    execute: Execute,
    generator: DataGenerator,
):
    artefact = generator.gen_artefact("beta")
    environment = generator.gen_environment()
    artefact_build = generator.gen_artefact_build(artefact, revision=1)

    request = StartSnapTestExecutionRequest(
        family=FamilyName.SNAP,
        name=artefact.name,
        version=artefact.version,
        revision=1,
        track=artefact.track,
        store=artefact.store,
        arch=artefact_build.architecture,
        execution_stage=artefact.stage_name,
        environment=environment.name,
        ci_link="http://localhost/",
        test_plan="test plan",
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
    assert test_execution.test_plan == "test plan"


def test_new_artefacts_get_assigned_a_reviewer(
    db_session: Session, execute: Execute, generator: DataGenerator
):
    user = generator.gen_user()

    execute(snap_test_request)

    artefact = db_session.query(Artefact).filter(Artefact.name == "core22").one()
    assert artefact.assignee is not None
    assert artefact.assignee.launchpad_handle == user.launchpad_handle


def test_non_kernel_artefact_due_date(db_session: Session, execute: Execute):
    """
    For non-kernel snaps, the default due date should be set to now + 10 days
    """
    execute(snap_test_request)

    artefact = (
        db_session.query(Artefact)
        .filter(
            Artefact.name == snap_test_request["name"],
            Artefact.version == snap_test_request["version"],
            Artefact.store == snap_test_request["store"],
            Artefact.track == snap_test_request["track"],
            Artefact.stage.has(name=snap_test_request["execution_stage"]),
        )
        .one_or_none()
    )

    assert artefact is not None
    assert artefact.due_date == date.today() + timedelta(10)


def test_kernel_artefact_due_date(db_session: Session, execute: Execute):
    """
    For kernel artefacts, due date shouldn't be set to default
    """
    request = {**snap_test_request, "name": "pi-kernel"}
    execute(request)

    artefact = (
        db_session.query(Artefact)
        .filter(
            Artefact.name == request["name"],
            Artefact.version == request["version"],
            Artefact.store == request["store"],
            Artefact.track == request["track"],
            Artefact.stage.has(name=request["execution_stage"]),
        )
        .one_or_none()
    )

    assert artefact is not None
    assert artefact.due_date is None


def test_deletes_rerun_requests(
    execute: Execute, generator: DataGenerator, db_session: Session
):
    a = generator.gen_artefact("beta")
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment()
    te1 = generator.gen_test_execution(ab, e, ci_link="ci1.link")
    te2 = generator.gen_test_execution(ab, e, ci_link="ci2.link")
    generator.gen_rerun_request(te1)
    generator.gen_rerun_request(te2)

    execute(
        {
            "family": a.family_name,
            "name": a.name,
            "version": a.version,
            "revision": ab.revision,
            "track": a.track,
            "store": a.store,
            "arch": ab.architecture,
            "execution_stage": a.stage_name,
            "environment": e.name,
            "ci_link": "different-ci.link",
            "test_plan": te1.test_plan,
        },
    )

    db_session.refresh(te1)
    db_session.refresh(te2)
    assert not te1.rerun_request
    assert not te2.rerun_request


def test_keeps_rerun_request_of_different_plan(
    execute: Execute, generator: DataGenerator, db_session: Session
):
    a = generator.gen_artefact("beta")
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment()
    te = generator.gen_test_execution(ab, e, ci_link="ci1.link", test_plan="plan1")
    generator.gen_rerun_request(te)

    execute(
        {
            "family": a.family_name,
            "name": a.name,
            "version": a.version,
            "revision": ab.revision,
            "track": a.track,
            "store": a.store,
            "arch": ab.architecture,
            "execution_stage": a.stage_name,
            "environment": e.name,
            "ci_link": "different-ci.link",
            "test_plan": "plan2",
        },
    )

    db_session.refresh(te)
    assert te.rerun_request


def test_sets_initial_test_execution_status(db_session: Session, execute: Execute):
    response = execute({**deb_test_request, "initial_status": "NOT_STARTED"})

    assert response.status_code == 200
    te = db_session.get(TestExecution, response.json()["id"])
    assert te is not None
    assert te.status == TestExecutionStatus.NOT_STARTED
