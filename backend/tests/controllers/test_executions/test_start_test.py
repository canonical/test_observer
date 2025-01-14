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
    TestExecution,
)
from test_observer.data_access.models_enums import (
    FamilyName,
    StageName,
    TestExecutionStatus,
)
from tests.asserts import assert_fails_validation
from tests.data_generator import DataGenerator

Execute: TypeAlias = Callable[[dict[str, Any]], Response]
Assert: TypeAlias = Callable[[dict[str, Any], Response], None]


snap_test_request = {
    "family": "snap",
    "name": "core22",
    "version": "abec123",
    "revision": 123,
    "track": "22",
    "store": "ubuntu",
    "arch": "arm64",
    "execution_stage": StageName.beta,
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
    "execution_stage": StageName.proposed,
    "arch": "amd64",
    "environment": "xps",
    "ci_link": "http://localhost",
    "test_plan": "test plan",
}

charm_test_request = {
    "family": "charm",
    "name": "postgresql",
    "version": "abec123",
    "revision": 123,
    "track": "22",
    "arch": "arm64",
    "execution_stage": StageName.beta,
    "environment": "juju 3 - microk8s 2",
    "ci_link": "http://localhost",
    "test_plan": "test plan",
}

image_test_request = {
    "family": "image",
    "name": "noble-desktop-amd64",
    "os": "ubuntu",
    "release": "noble",
    "arch": "amd64",
    "version": "20240827",
    "sha256": "e71fb5681e63330445eec6fc3fe043f365289c2e595e3ceeac08fbeccfb9a957",
    "owner": "foundations",
    "image_url": "https://cdimage.ubuntu.com/noble/daily-live/20240827/noble-desktop-amd64.iso",
    "execution_stage": StageName.pending,
    "test_plan": "image test plan",
    "environment": "xps",
    "ci_link": "http://localhost",
}


@pytest.mark.parametrize(
    "start_request",
    [snap_test_request, deb_test_request, charm_test_request, image_test_request],
)
class TestStartTest:
    def test_starts_a_test(self, execute: Execute, start_request: dict[str, Any]):
        response = execute(start_request)
        self._assert_objects_created(start_request, response)

    def test_requires_family_field(
        self, execute: Execute, start_request: dict[str, Any]
    ):
        request = start_request.copy()
        request.pop("family")
        response = execute(request)

        assert response.status_code == 422

    @pytest.fixture(autouse=True)
    def _set_db_session(self, db_session: Session) -> None:
        self._db_session = db_session

    def _assert_objects_created(
        self, request: dict[str, Any], response: Response
    ) -> None:
        assert response.status_code == 200
        test_execution = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        assert test_execution.ci_link == request["ci_link"]
        assert test_execution.test_plan == request["test_plan"]
        assert test_execution.status == request.get(
            "initial_status", TestExecutionStatus.IN_PROGRESS
        )

        environment = test_execution.environment
        assert environment.architecture == request["arch"]
        assert environment.name == request["environment"]

        artefact_build = test_execution.artefact_build
        assert artefact_build.architecture == request["arch"]
        assert artefact_build.revision == request.get("revision")

        artefact = artefact_build.artefact
        assert artefact.name == request["name"]
        assert artefact.family == request["family"]
        assert artefact.stage == request["execution_stage"]
        assert artefact.version == request["version"]
        assert artefact.os == request.get("os", "")
        assert artefact.release == request.get("release", "")
        assert artefact.sha256 == request.get("sha256", "")
        assert artefact.owner == request.get("owner", "")
        assert artefact.image_url == request.get("image_url", "")
        assert artefact.store == request.get("store", "")
        assert artefact.track == request.get("track", "")
        assert artefact.series == request.get("series", "")
        assert artefact.repo == request.get("repo", "")


@pytest.fixture
def execute(test_client: TestClient) -> Execute:
    def execute_helper(data: dict[str, Any]) -> Response:
        return test_client.put("/v1/test-executions/start-test", json=data)

    return execute_helper


@pytest.mark.parametrize(
    "field",
    [
        "name",
        "version",
        "revision",
        "arch",
        "execution_stage",
        "environment",
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
        "test_plan",
    ],
)
def test_deb_required_fields(execute: Execute, field: str):
    request = deb_test_request.copy()
    request.pop(field)
    response = execute(request)

    assert_fails_validation(response, field, "missing")


@pytest.mark.parametrize(
    "field",
    [
        "name",
        "version",
        "track",
        "revision",
        "arch",
        "execution_stage",
        "environment",
        "ci_link",
        "test_plan",
    ],
)
def test_charm_required_fields(execute: Execute, field: str):
    request = charm_test_request.copy()
    request.pop(field)
    response = execute(request)

    assert_fails_validation(response, field, "missing")


@pytest.mark.parametrize(
    "field",
    [
        "name",
        "version",
        "os",
        "release",
        "arch",
        "sha256",
        "owner",
        "image_url",
        "execution_stage",
        "environment",
        "ci_link",
    ],
)
def test_image_required_fields(execute: Execute, field: str):
    request = image_test_request.copy()
    request.pop(field)
    response = execute(request)

    assert_fails_validation(response, field, "missing")


def test_uses_existing_models(
    db_session: Session,
    execute: Execute,
    generator: DataGenerator,
):
    artefact = generator.gen_artefact(StageName.beta)
    environment = generator.gen_environment()
    artefact_build = generator.gen_artefact_build(artefact, revision=1)

    request = StartSnapTestExecutionRequest(
        family=FamilyName.snap,
        name=artefact.name,
        version=artefact.version,
        revision=1,
        track=artefact.track,
        store=artefact.store,
        arch=artefact_build.architecture,
        execution_stage=StageName.beta,
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
            Artefact.stage == snap_test_request["execution_stage"],
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
            Artefact.stage == request["execution_stage"],
        )
        .one_or_none()
    )

    assert artefact is not None
    assert artefact.due_date is None


def test_deletes_rerun_requests(
    execute: Execute, generator: DataGenerator, db_session: Session
):
    a = generator.gen_artefact(StageName.beta)
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment()
    te1 = generator.gen_test_execution(ab, e, ci_link="ci1.link")
    te2 = generator.gen_test_execution(ab, e, ci_link="ci2.link")
    generator.gen_rerun_request(te1)
    generator.gen_rerun_request(te2)

    execute(
        {
            "family": a.family,
            "name": a.name,
            "version": a.version,
            "revision": ab.revision,
            "track": a.track,
            "store": a.store,
            "arch": ab.architecture,
            "execution_stage": a.stage,
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
    a = generator.gen_artefact(StageName.beta)
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment()
    te = generator.gen_test_execution(ab, e, ci_link="ci1.link", test_plan="plan1")
    generator.gen_rerun_request(te)

    execute(
        {
            "family": a.family,
            "name": a.name,
            "version": a.version,
            "revision": ab.revision,
            "track": a.track,
            "store": a.store,
            "arch": ab.architecture,
            "execution_stage": a.stage,
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


def test_allows_null_ci_link(db_session: Session, execute: Execute):
    request = {**deb_test_request, "ci_link": None}

    response = execute(request)

    assert response.status_code == 200
    te = db_session.get(TestExecution, response.json()["id"])
    assert te is not None
    assert te.ci_link is None


def test_allows_omitting_ci_link(db_session: Session, execute: Execute):
    request = {**deb_test_request}
    del request["ci_link"]

    response = execute(request)

    assert response.status_code == 200
    te = db_session.get(TestExecution, response.json()["id"])
    assert te is not None
    assert te.ci_link is None


def test_create_two_executions_for_null_ci_link(execute: Execute):
    request = {**deb_test_request}
    del request["ci_link"]

    response_1 = execute(request)
    response_2 = execute(request)

    assert response_1.status_code == 200
    assert response_2.status_code == 200
    assert response_1.json()["id"] != response_2.json()["id"]


@pytest.mark.parametrize(
    "an_invalid_stage",
    set(StageName) - {StageName.proposed, StageName.updates},
)
def test_validates_stage_for_debs(execute: Execute, an_invalid_stage: StageName):
    response = execute({**deb_test_request, "execution_stage": an_invalid_stage})

    assert response.status_code == 422


@pytest.mark.parametrize(
    "an_invalid_stage",
    set(StageName)
    - {
        StageName.edge,
        StageName.beta,
        StageName.candidate,
        StageName.stable,
    },
)
def test_validates_stage_for_snaps(execute: Execute, an_invalid_stage: StageName):
    response = execute({**snap_test_request, "execution_stage": an_invalid_stage})

    assert response.status_code == 422


@pytest.mark.parametrize(
    "an_invalid_stage",
    set(StageName)
    - {
        StageName.edge,
        StageName.beta,
        StageName.candidate,
        StageName.stable,
    },
)
def test_validates_stage_for_charms(execute: Execute, an_invalid_stage: StageName):
    response = execute({**charm_test_request, "execution_stage": an_invalid_stage})

    assert response.status_code == 422
