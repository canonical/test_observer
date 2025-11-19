# Copyright (C) 2023 Canonical Ltd.
#
# This file is part of Test Observer Backend.
#
# Test Observer Backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# Test Observer Backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy.orm import Session

from test_observer.data_access.models import (
    TestExecution,
    ReviewerPool,
)
from test_observer.data_access.models_enums import (
    SnapStage,
    DebStage,
    CharmStage,
    ImageStage,
    TestExecutionStatus,
)
from test_observer.common.permissions import Permission
from tests.data_generator import DataGenerator
from tests.conftest import make_authenticated_request

type Execute = Callable[[dict[str, Any]], Response]


@pytest.fixture
def execute(test_client: TestClient) -> Execute:
    def execute_helper(data: dict[str, Any]) -> Response:
        return make_authenticated_request(
            lambda: test_client.put("/v1/test-executions/start-test", json=data),
            Permission.change_test,
        )

    return execute_helper


snap_test_request = {
    "family": "snap",
    "name": "core22",
    "version": "abec123",
    "revision": 123,
    "track": "22",
    "store": "ubuntu",
    "arch": "arm64",
    "execution_stage": SnapStage.beta,
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
    "execution_stage": DebStage.proposed,
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
    "execution_stage": CharmStage.beta,
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
    "execution_stage": ImageStage.pending,
    "test_plan": "image test plan",
    "environment": "xps",
    "ci_link": "http://localhost",
}


@pytest.mark.parametrize(
    "start_request",
    [snap_test_request, deb_test_request, charm_test_request, image_test_request],
)
class TestFamilyIndependentTests:
    def test_starts_a_test(self, execute: Execute, start_request: dict[str, Any]):
        response = execute(start_request)
        self._assert_objects_created(response)

    def test_requires_family_field(
        self, execute: Execute, start_request: dict[str, Any]
    ):
        request = start_request.copy()
        request.pop("family")
        response = execute(request)

        assert response.status_code == 422

    def test_reuses_test_execution(
        self, execute: Execute, start_request: dict[str, Any]
    ):
        response = execute(start_request)

        test_execution = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution

        response = execute(start_request)
        assert response.json()["id"] == test_execution.id

    def test_reuses_environment_and_build(
        self, execute: Execute, start_request: dict[str, Any]
    ):
        response = execute(start_request)
        test_execution_1 = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution_1

        response = execute({**start_request, "ci_link": "http://someother.link"})
        test_execution_2 = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution_2

        assert test_execution_2.id != test_execution_1.id
        assert test_execution_2.environment_id == test_execution_1.environment_id
        assert test_execution_2.artefact_build_id == test_execution_1.artefact_build_id

    def test_new_artefact_no_assignment_and_no_date_by_default(
        self, execute: Execute, generator: DataGenerator, start_request: dict[str, Any]
    ):
        generator.gen_user()

        response = execute(start_request)

        test_execution = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        assert test_execution.artefact_build.artefact.assignee is None
        assert test_execution.artefact_build.artefact.due_date is None

    def test_new_artefacts_get_assigned_a_reviewer(
        self,
        execute: Execute,
        generator: DataGenerator,
        start_request: dict[str, Any],
        db_session: Session,
    ):
        user = generator.gen_user(is_reviewer=True)

        pool_name = "sqa" if start_request["family"] == "charm" else "cert"
        pool = db_session.query(ReviewerPool).filter_by(name=pool_name).first()
        if pool and user not in pool.members:
            pool.members.append(user)
            db_session.commit()

        response = execute({**start_request, "needs_assignment": True})

        test_execution = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        assignee = test_execution.artefact_build.artefact.assignee
        assert assignee is not None
        assert assignee.launchpad_handle == user.launchpad_handle

    def test_only_a_reviewer_user_is_assigned(
        self, execute: Execute, generator: DataGenerator, start_request: dict[str, Any]
    ):
        generator.gen_user()

        response = execute({**start_request, "needs_assignment": True})

        test_execution = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        assignee = test_execution.artefact_build.artefact.assignee
        assert assignee is None

    def test_deletes_rerun_requests(
        self, execute: Execute, generator: DataGenerator, start_request: dict[str, Any]
    ):
        response = execute(start_request)

        test_execution = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution

        generator.gen_rerun_request(test_execution)
        assert test_execution.rerun_request

        execute({**start_request, "ci_link": "http://someother.link"})
        self._db_session.refresh(test_execution)
        assert not test_execution.rerun_request

    def test_keeps_rerun_request_of_different_plan(
        self, execute: Execute, generator: DataGenerator, start_request: dict[str, Any]
    ):
        response = execute(start_request)

        test_execution = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution

        generator.gen_rerun_request(test_execution)
        assert test_execution.rerun_request

        execute(
            {
                **start_request,
                "ci_link": "http://someother.link",
                "test_plan": "different plan",
            }
        )
        self._db_session.refresh(test_execution)
        assert test_execution.rerun_request

    def test_sets_initial_test_execution_status(
        self, execute: Execute, start_request: dict[str, Any]
    ):
        response = execute({**start_request, "initial_status": "NOT_STARTED"})

        assert response.status_code == 200
        te = self._db_session.get(TestExecution, response.json()["id"])
        assert te is not None
        assert te.status == TestExecutionStatus.NOT_STARTED

    @pytest.fixture(autouse=True)
    def _set_db_session(self, db_session: Session) -> None:
        self._db_session = db_session

    @staticmethod
    def _assert_objects_created(response: Response) -> None:
        assert response.status_code == 200
        response_body = response.json()
        assert "id" in response_body


class TestReviewerPoolAssignment:
    """Test assignment logic with reviewer pools"""

    def test_charm_assigned_from_sqa_pool(
        self, execute: Execute, generator: DataGenerator, db_session: Session
    ):
        """Charms should be assigned from SQA pool"""
        # Create a reviewer and add to SQA pool
        user = generator.gen_user(
            is_reviewer=True, email="charm_reviewer@canonical.com"
        )
        sqa_pool = db_session.query(ReviewerPool).filter_by(name="sqa").first()
        assert sqa_pool is not None
        if user not in sqa_pool.members:
            sqa_pool.members.append(user)
            db_session.commit()

        # Create charm with assignment
        response = execute({**charm_test_request, "needs_assignment": True})

        assert response.status_code == 200
        test_execution = db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        assignee = test_execution.artefact_build.artefact.assignee
        assert assignee is not None
        assert assignee.id == user.id

    def test_snap_assigned_from_cert_pool(
        self, execute: Execute, generator: DataGenerator, db_session: Session
    ):
        """Snaps should be assigned from cert pool"""
        user = generator.gen_user(is_reviewer=True, email="snap_reviewer@canonical.com")
        cert_pool = db_session.query(ReviewerPool).filter_by(name="cert").first()
        assert cert_pool is not None
        if user not in cert_pool.members:
            cert_pool.members.append(user)
            db_session.commit()

        response = execute({**snap_test_request, "needs_assignment": True})

        assert response.status_code == 200
        test_execution = db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        assignee = test_execution.artefact_build.artefact.assignee
        assert assignee is not None
        assert assignee.id == user.id

    def test_deb_assigned_from_cert_pool(
        self, execute: Execute, generator: DataGenerator, db_session: Session
    ):
        """Debs should be assigned from cert pool"""
        user = generator.gen_user(is_reviewer=True, email="deb_reviewer@canonical.com")
        cert_pool = db_session.query(ReviewerPool).filter_by(name="cert").first()
        assert cert_pool is not None
        if user not in cert_pool.members:
            cert_pool.members.append(user)
            db_session.commit()

        response = execute({**deb_test_request, "needs_assignment": True})

        assert response.status_code == 200
        test_execution = db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        assignee = test_execution.artefact_build.artefact.assignee
        assert assignee is not None
        assert assignee.id == user.id

    def test_image_assigned_from_cert_pool(
        self, execute: Execute, generator: DataGenerator, db_session: Session
    ):
        """Images should be assigned from cert pool"""
        user = generator.gen_user(
            is_reviewer=True, email="image_reviewer@canonical.com"
        )
        cert_pool = db_session.query(ReviewerPool).filter_by(name="cert").first()
        assert cert_pool is not None
        if user not in cert_pool.members:
            cert_pool.members.append(user)
            db_session.commit()

        response = execute({**image_test_request, "needs_assignment": True})

        assert response.status_code == 200
        test_execution = db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        assignee = test_execution.artefact_build.artefact.assignee
        assert assignee is not None
        assert assignee.id == user.id

    def test_charm_not_assigned_when_pool_empty(
        self, execute: Execute, db_session: Session
    ):
        """Charm not assigned if SQA pool has no reviewers"""
        # Ensure SQA pool exists but has no members
        sqa_pool = db_session.query(ReviewerPool).filter_by(name="sqa").first()
        assert sqa_pool is not None
        sqa_pool.members.clear()
        db_session.commit()

        response = execute({**charm_test_request, "needs_assignment": True})

        assert response.status_code == 200
        test_execution = db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        assignee = test_execution.artefact_build.artefact.assignee
        assert assignee is None

    def test_snap_not_assigned_when_pool_empty(
        self, execute: Execute, db_session: Session
    ):
        """Snap not assigned if cert pool has no reviewers"""
        cert_pool = db_session.query(ReviewerPool).filter_by(name="cert").first()
        assert cert_pool is not None
        cert_pool.members.clear()
        db_session.commit()

        response = execute({**snap_test_request, "needs_assignment": True})

        assert response.status_code == 200
        test_execution = db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        assignee = test_execution.artefact_build.artefact.assignee
        assert assignee is None

    def test_only_reviewer_users_in_pool_can_be_assigned(
        self, execute: Execute, generator: DataGenerator, db_session: Session
    ):
        """Only users with is_reviewer=True in pool should be assigned"""
        # Add non-reviewer user to cert pool
        user = generator.gen_user(is_reviewer=False, email="non_reviewer@canonical.com")
        cert_pool = db_session.query(ReviewerPool).filter_by(name="cert").first()
        assert cert_pool is not None
        if user not in cert_pool.members:
            cert_pool.members.append(user)
            db_session.commit()

        response = execute({**snap_test_request, "needs_assignment": True})

        assert response.status_code == 200
        test_execution = db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        assignee = test_execution.artefact_build.artefact.assignee
        assert assignee is None

    def test_assignment_randomly_selects_from_pool(
        self, execute: Execute, generator: DataGenerator, db_session: Session
    ):
        """Assignment should randomly select from pool members"""
        users = []
        for i in range(3):
            user = generator.gen_user(is_reviewer=True)
            user.email = f"reviewer{i}@canonical.com"
            db_session.add(user)
            db_session.commit()
            users.append(user)

        cert_pool = db_session.query(ReviewerPool).filter_by(name="cert").first()
        assert cert_pool is not None
        for user in users:
            if user not in cert_pool.members:
                cert_pool.members.append(user)
        db_session.commit()

        assignees = set()
        for i in range(10):
            response = execute(
                {
                    **snap_test_request,
                    "needs_assignment": True,
                    "ci_link": f"http://localhost/snap{i}",
                }
            )
            assert response.status_code == 200
            test_execution = db_session.get(TestExecution, response.json()["id"])
            assert test_execution is not None
            assignee = test_execution.artefact_build.artefact.assignee
            if assignee:
                assignees.add(assignee.id)

        assert len(assignees) >= 1
        assert all(user_id in [u.id for u in users] for user_id in assignees)

    @pytest.fixture(autouse=True)
    def _set_db_session(self, db_session: Session) -> None:
        self._db_session = db_session
