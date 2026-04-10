# Copyright 2024 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy.orm import Session

from test_observer.common.enums import Permission
from test_observer.common.review_notification import (
    create_reviewer_notification,
)
from test_observer.data_access.models import (
    Artefact,
    Notification,
    TestExecution,
)
from test_observer.data_access.models_enums import (
    CharmStage,
    DebStage,
    FamilyName,
    ImageStage,
    NotificationType,
    SnapStage,
    StageName,
    TestExecutionStatus,
)
from tests.asserts import assert_fails_validation
from tests.conftest import make_authenticated_request
from tests.data_generator import DataGenerator

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
        self._assert_objects_created(start_request, response)

    def test_requires_family_field(self, execute: Execute, start_request: dict[str, Any]):
        request = start_request.copy()
        request.pop("family")
        response = execute(request)

        assert response.status_code == 422

    def test_reuses_test_execution(self, execute: Execute, start_request: dict[str, Any]):
        response = execute(start_request)

        test_execution = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution

        response = execute(start_request)
        assert response.json()["id"] == test_execution.id

    def test_reuses_environment_and_build(self, execute: Execute, start_request: dict[str, Any]):
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
        assert test_execution.artefact_build.artefact.reviewers == []
        assert test_execution.artefact_build.artefact.due_date is None

    def test_new_artefacts_get_assigned_a_reviewer(
        self, execute: Execute, generator: DataGenerator, start_request: dict[str, Any]
    ):
        # Create a team with matching rules for all families
        snap_rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
        deb_rule = generator.gen_artefact_matching_rule(family=FamilyName.deb)
        charm_rule = generator.gen_artefact_matching_rule(family=FamilyName.charm)
        image_rule = generator.gen_artefact_matching_rule(family=FamilyName.image)

        team = generator.gen_team(
            name="reviewers",
            artefact_matching_rules=[snap_rule, deb_rule, charm_rule, image_rule],
        )
        # User is member of this team
        user = generator.gen_user(teams=[team])

        response = execute({**start_request, "needs_assignment": True})

        test_execution = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        assignee = (
            test_execution.artefact_build.artefact.reviewers[0]
            if test_execution.artefact_build.artefact.reviewers
            else None
        )
        assert assignee is not None
        assert assignee.launchpad_handle == user.launchpad_handle

    def test_only_a_reviewer_user_is_assigned(
        self, execute: Execute, generator: DataGenerator, start_request: dict[str, Any]
    ):
        # User with no teams cannot be assigned as reviewer
        generator.gen_user()

        response = execute({**start_request, "needs_assignment": True})

        test_execution = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        assignee = (
            test_execution.artefact_build.artefact.reviewers[0]
            if test_execution.artefact_build.artefact.reviewers
            else None
        )
        assert assignee is None

    def test_artefact_with_few_environments_gets_assigned_single_reviewer(
        self, execute: Execute, generator: DataGenerator, start_request: dict[str, Any]
    ):
        """
        Assert that an artefact with only 1 environment
        gets assigned to a single reviewer even if multiple are available
        """
        # Create a team that can review all families
        snap_rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
        deb_rule = generator.gen_artefact_matching_rule(family=FamilyName.deb)
        charm_rule = generator.gen_artefact_matching_rule(family=FamilyName.charm)
        image_rule = generator.gen_artefact_matching_rule(family=FamilyName.image)
        team = generator.gen_team(
            name="reviewers",
            artefact_matching_rules=[snap_rule, deb_rule, charm_rule, image_rule],
        )
        # Create multiple users who can review
        generator.gen_user(email="user1@example.com", teams=[team])
        generator.gen_user(email="user2@example.com", teams=[team])
        generator.gen_user(email="user3@example.com", teams=[team])

        response = execute({**start_request, "needs_assignment": True})

        test_execution = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        # Verify the artefact has only 1 environment
        artefact = test_execution.artefact_build.artefact
        assert len(artefact.builds) == 1
        assert len(artefact.builds[0].environment_reviews) == 1
        # Even with multiple reviewers available, only one should be assigned
        assert len(artefact.reviewers) == 1

    def test_artefact_with_many_environments_is_assigned_multiple_reviewers(
        self, execute: Execute, generator: DataGenerator, start_request: dict[str, Any]
    ):
        """Assert that an artefact with more than 50 environments is assigned more than one reviewer"""
        # Create a team that can review all families
        snap_rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
        deb_rule = generator.gen_artefact_matching_rule(family=FamilyName.deb)
        charm_rule = generator.gen_artefact_matching_rule(family=FamilyName.charm)
        image_rule = generator.gen_artefact_matching_rule(family=FamilyName.image)
        team = generator.gen_team(
            name="reviewers",
            artefact_matching_rules=[snap_rule, deb_rule, charm_rule, image_rule],
        )
        # Create multiple users who can review
        generator.gen_user(email="user1@example.com", teams=[team])
        generator.gen_user(email="user2@example.com", teams=[team])

        # Execute the first test to create the artefact
        response = execute({**start_request, "needs_assignment": True})
        test_execution = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        artefact = test_execution.artefact_build.artefact

        # Now create 50+ more environments for the same artefact by executing tests with different environment names
        for i in range(51):
            env_request = {
                **start_request,
                "environment": f"env-{i}",
                "ci_link": f"http://localhost/{i}",
                "needs_assignment": False,  # Don't trigger assignment for these
            }
            execute(env_request)

        # Clear reviewers to allow reassignment based on the new environment count
        artefact.reviewers = []
        self._db_session.commit()

        # Trigger assignment again now that we have 52 environments
        execute({**start_request, "environment": "final-env", "ci_link": "http://final", "needs_assignment": True})

        # Refresh the artefact to get updated relationships
        self._db_session.refresh(artefact)

        # Verify the artefact now has more than 50 environments (52 from before + 1 new = 53)
        assert artefact.all_environment_reviews_count == 53

        assert len(artefact.reviewers) == 2

    def test_multiple_reviewers_assigned_to_environment_reviews(
        self, execute: Execute, generator: DataGenerator, start_request: dict[str, Any]
    ):
        """
        When multiple reviewers are assigned to an artefact,
        each environment review should get exactly one reviewer assigned,
        with reviewers from an artefact distributed across environment
        reviews based on current assignment counts.
        """
        # Create a team that can review all families
        snap_rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
        deb_rule = generator.gen_artefact_matching_rule(family=FamilyName.deb)
        charm_rule = generator.gen_artefact_matching_rule(family=FamilyName.charm)
        image_rule = generator.gen_artefact_matching_rule(family=FamilyName.image)
        team = generator.gen_team(
            name="reviewers",
            artefact_matching_rules=[snap_rule, deb_rule, charm_rule, image_rule],
        )
        # Create 3 users who can review
        generator.gen_user(email="user1@example.com", teams=[team])
        generator.gen_user(email="user2@example.com", teams=[team])
        generator.gen_user(email="user3@example.com", teams=[])

        # Execute the first test to create the artefact
        response = execute({**start_request, "needs_assignment": True})
        test_execution = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        artefact = test_execution.artefact_build.artefact

        # Create 50+ more environments to trigger multiple reviewer assignment
        for i in range(51):
            env_request = {
                **start_request,
                "environment": f"env-{i}",
                "ci_link": f"http://localhost/{i}",
                "needs_assignment": False,
            }
            execute(env_request)

        # Clear reviewers to allow reassignment
        artefact.reviewers = []
        self._db_session.commit()

        # Trigger assignment again now that we have 52 environments
        execute({**start_request, "environment": "final-env", "ci_link": "http://final", "needs_assignment": True})

        # Refresh the artefact to get updated relationships
        self._db_session.refresh(artefact)

        # Verify multiple reviewers were assigned
        assert len(artefact.reviewers) == 2

        # Verify each environment review has exactly one reviewer
        for build in artefact.builds:
            for env_review in build.environment_reviews:
                assert len(env_review.reviewers) == 1, (
                    f"Environment review {env_review.id} should have exactly 1 reviewer"
                )
                # Verify the assigned reviewer is from the artefact's reviewers
                assert env_review.reviewers[0] in artefact.reviewers, (
                    f"Reviewer {env_review.reviewers[0].email} not in artefact reviewers"
                )

    def test_environment_reviewers_distributed_across_multiple_builds(
        self, execute: Execute, generator: DataGenerator, start_request: dict[str, Any]
    ):
        """
        When an artefact has multiple builds and multiple reviewers,
        each build's environment reviews should get reviewer assignments
        """
        # Create a team that can review all families
        snap_rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
        deb_rule = generator.gen_artefact_matching_rule(family=FamilyName.deb)
        charm_rule = generator.gen_artefact_matching_rule(family=FamilyName.charm)
        image_rule = generator.gen_artefact_matching_rule(family=FamilyName.image)
        team = generator.gen_team(
            name="reviewers",
            artefact_matching_rules=[snap_rule, deb_rule, charm_rule, image_rule],
        )
        generator.gen_user(email="user1@example.com", teams=[team])
        generator.gen_user(email="user2@example.com", teams=[team])

        # Execute test for first architecture
        response = execute({**start_request, "needs_assignment": True})
        test_execution = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        artefact = test_execution.artefact_build.artefact

        # Create 50+ more environments with different architectures
        for i in range(26):
            env_request = {
                **start_request,
                "arch": "amd64",
                "environment": f"env-amd64-{i}",
                "ci_link": f"http://localhost/amd64/{i}",
                "needs_assignment": False,
            }
            execute(env_request)

        for i in range(26):
            env_request = {
                **start_request,
                "arch": "arm64",
                "environment": f"env-arm64-{i}",
                "ci_link": f"http://localhost/arm64/{i}",
                "needs_assignment": False,
            }
            execute(env_request)

        # Clear reviewers to allow reassignment
        artefact.reviewers = []
        self._db_session.commit()

        # Trigger assignment again
        execute({**start_request, "environment": "final-env", "ci_link": "http://final", "needs_assignment": True})

        # Refresh the artefact
        self._db_session.refresh(artefact)

        # Verify multiple reviewers assigned
        assert len(artefact.reviewers) >= 2

        # Verify we have multiple builds
        assert len(artefact.builds) >= 2

        # Verify each build's environment reviews have reviewers assigned
        for build in artefact.builds:
            if len(build.environment_reviews) > 0:
                for env_review in build.environment_reviews:
                    assert len(env_review.reviewers) == 1, (
                        f"Environment review {env_review.id} in build {build.id} should have exactly 1 reviewer"
                    )

    def test_reviewers_equally_distributed(
        self, execute: Execute, generator: DataGenerator, start_request: dict[str, Any]
    ):
        """
        When multiple reviewers are assigned to an artefact,
        environment reviews should be distributed equally among reviewers
        based on ceiling division of total reviews by number of reviewers
        """
        # Create a team that can review all families
        snap_rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
        deb_rule = generator.gen_artefact_matching_rule(family=FamilyName.deb)
        charm_rule = generator.gen_artefact_matching_rule(family=FamilyName.charm)
        image_rule = generator.gen_artefact_matching_rule(family=FamilyName.image)
        team = generator.gen_team(
            name="reviewers",
            artefact_matching_rules=[snap_rule, deb_rule, charm_rule, image_rule],
        )
        # Create 3 users who can review
        _ = generator.gen_user(email="user1@example.com", teams=[team])
        _ = generator.gen_user(email="user2@example.com", teams=[team])
        _ = generator.gen_user(email="user3@example.com", teams=[team])

        # Execute the first test to create the artefact
        response = execute({**start_request, "needs_assignment": True})
        test_execution = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        artefact = test_execution.artefact_build.artefact

        # Create 50+ more environments to trigger multiple reviewer assignment
        for i in range(51):
            env_request = {
                **start_request,
                "environment": f"env-{i}",
                "ci_link": f"http://localhost/{i}",
                "needs_assignment": False,
            }
            execute(env_request)

        # Clear reviewers to allow reassignment
        artefact.reviewers = []
        self._db_session.commit()

        # Trigger assignment again now that we have 52 environments
        execute({**start_request, "environment": "final-env", "ci_link": "http://final", "needs_assignment": True})

        # Refresh the artefact to get updated relationships
        self._db_session.refresh(artefact)

        # Verify multiple reviewers were assigned
        assert len(artefact.reviewers) == 2

        # Count assignments per reviewer
        reviewer_assignment_counts = {reviewer.id: 0 for reviewer in artefact.reviewers}
        total_env_reviews = 0

        for build in artefact.builds:
            for env_review in build.environment_reviews:
                total_env_reviews += 1
                assert len(env_review.reviewers) == 1
                reviewer_id = env_review.reviewers[0].id
                if reviewer_id in reviewer_assignment_counts:
                    reviewer_assignment_counts[reviewer_id] += 1

        # Verify equal distribution: each reviewer should get ceil(total / num_reviewers)
        # With 53 environments and 2 reviewers: ceil(53/2) = 27
        expected_max_per_reviewer = (total_env_reviews + len(artefact.reviewers) - 1) // len(artefact.reviewers)
        expected_min_per_reviewer = total_env_reviews // len(artefact.reviewers)

        for reviewer_id, count in reviewer_assignment_counts.items():
            assert expected_min_per_reviewer <= count <= expected_max_per_reviewer, (
                f"Reviewer {reviewer_id} has {count} assignments, "
                f"expected between {expected_min_per_reviewer} and {expected_max_per_reviewer}"
            )

        # Verify all reviews were assigned
        assert sum(reviewer_assignment_counts.values()) == total_env_reviews

    def test_deletes_rerun_requests(self, execute: Execute, generator: DataGenerator, start_request: dict[str, Any]):
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

    def test_sets_initial_test_execution_status(self, execute: Execute, start_request: dict[str, Any]):
        response = execute({**start_request, "initial_status": "NOT_STARTED"})

        assert response.status_code == 200
        te = self._db_session.get(TestExecution, response.json()["id"])
        assert te is not None
        assert te.status == TestExecutionStatus.NOT_STARTED

    def test_start_test_with_needs_assignment_creates_notifications(
        self, execute: Execute, generator: DataGenerator, start_request: dict[str, Any]
    ):
        """When starting test with needs_assignment=true, notifications should be created for environment reviewers"""
        # Create a team with matching rules for all families
        snap_rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
        deb_rule = generator.gen_artefact_matching_rule(family=FamilyName.deb)
        charm_rule = generator.gen_artefact_matching_rule(family=FamilyName.charm)
        image_rule = generator.gen_artefact_matching_rule(family=FamilyName.image)

        team = generator.gen_team(
            name="reviewers",
            artefact_matching_rules=[snap_rule, deb_rule, charm_rule, image_rule],
        )
        # Create users on the team
        generator.gen_user(email="reviewer1@example.com", teams=[team])
        generator.gen_user(email="reviewer2@example.com", teams=[team])

        # Execute test with automatic assignment
        response = execute({**start_request, "needs_assignment": True})

        test_execution = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        assert len(test_execution.artefact_build.artefact.reviewers) > 0

        # Get all notifications for the assigned reviewers
        assigned_reviewer_ids = [r.id for r in test_execution.artefact_build.artefact.reviewers]
        notifications = (
            self._db_session.query(Notification)
            .filter(
                Notification.user_id.in_(assigned_reviewer_ids),
                Notification.notification_type == NotificationType.USER_ASSIGNED_ENVIRONMENT_REVIEW,
            )
            .all()
        )

        # Should have notifications for environment reviews (at least one per reviewer)
        assert len(notifications) == len(assigned_reviewer_ids)
        # Verify notifications are for the right type
        assert all(n.notification_type == NotificationType.USER_ASSIGNED_ENVIRONMENT_REVIEW for n in notifications)

    def test_start_test_without_needs_assignment_no_notifications(
        self, execute: Execute, start_request: dict[str, Any]
    ):
        """When starting test with needs_assignment=false, no reviewer notifications should be created"""
        # Clear any existing notifications
        self._db_session.query(Notification).delete()
        self._db_session.commit()

        # Execute test WITHOUT automatic assignment
        response = execute({**start_request, "needs_assignment": False})

        test_execution = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution

        # Check that no environment review notifications were created
        notifications = (
            self._db_session.query(Notification)
            .filter(
                Notification.notification_type == NotificationType.USER_ASSIGNED_ENVIRONMENT_REVIEW,
            )
            .all()
        )

        assert len(notifications) == 0

    @pytest.fixture(autouse=True)
    def _set_db_session(self, db_session: Session) -> None:
        self._db_session = db_session

    def _assert_objects_created(self, request: dict[str, Any], response: Response) -> None:
        assert response.status_code == 200
        test_execution = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        assert test_execution.ci_link == request["ci_link"]
        assert test_execution.test_plan.name == request["test_plan"]
        assert test_execution.status == request.get("initial_status", TestExecutionStatus.IN_PROGRESS)

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
        assert artefact.image_url == str(request.get("image_url", ""))
        assert artefact.store == request.get("store", "")
        assert artefact.track == request.get("track", "")
        assert artefact.series == request.get("series", "")
        assert artefact.repo == request.get("repo", "")


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
    ],
)
def test_image_required_fields(execute: Execute, field: str):
    request = image_test_request.copy()
    request.pop(field)
    response = execute(request)

    assert_fails_validation(response, field, "missing")


def test_non_kernel_artefact_due_date(db_session: Session, execute: Execute, generator: DataGenerator):
    """
    For non-kernel snaps, the default due date should be set to now + 10 days
    """
    snap_rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)

    snap_reviewers = generator.gen_team(
        name="snap_reviewers",
        artefact_matching_rules=[snap_rule],
    )
    generator.gen_user(teams=[snap_reviewers])

    execute({**snap_test_request, "needs_assignment": True})

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


@pytest.mark.parametrize(
    "invalid_stage",
    set(StageName) - set(DebStage),
)
def test_validates_stage_for_debs(execute: Execute, invalid_stage: StageName):
    response = execute({**deb_test_request, "execution_stage": invalid_stage})

    assert response.status_code == 422


@pytest.mark.parametrize(
    "invalid_stage",
    set(StageName) - set(SnapStage),
)
def test_validates_stage_for_snaps(execute: Execute, invalid_stage: StageName):
    response = execute({**snap_test_request, "execution_stage": invalid_stage})

    assert response.status_code == 422


@pytest.mark.parametrize(
    "invalid_stage",
    set(StageName) - set(CharmStage),
)
def test_validates_stage_for_charms(execute: Execute, invalid_stage: StageName):
    response = execute({**charm_test_request, "execution_stage": invalid_stage})

    assert response.status_code == 422


def test_snap_branch_is_part_of_uniqueness(execute: Execute, db_session: Session):
    response = execute(snap_test_request)
    te1 = db_session.get(TestExecution, response.json()["id"])

    request_with_branch = {
        **snap_test_request,
        "branch": "test-branch",
        "ci_link": "http://someother.link",
    }
    response = execute(request_with_branch)
    te2 = db_session.get(TestExecution, response.json()["id"])

    assert te1 and te2
    assert te1.artefact_build.artefact_id != te2.artefact_build.artefact_id


def test_deb_source_is_part_of_uniqueness(execute: Execute, db_session: Session):
    response = execute(deb_test_request)
    te1 = db_session.get(TestExecution, response.json()["id"])

    request_with_source = {
        **deb_test_request,
        "source": "ppa",
        "ci_link": "http://someother.link",
    }
    request_with_source.pop("execution_stage")
    response = execute(request_with_source)
    te2 = db_session.get(TestExecution, response.json()["id"])

    assert te1 and te2
    assert te1.artefact_build.artefact_id != te2.artefact_build.artefact_id


def test_deb_without_source_must_have_a_stage(execute: Execute):
    request = {**deb_test_request}
    request.pop("execution_stage")
    response = execute(request)

    assert response.status_code == 422


def test_deb_with_source_and_no_stage(execute: Execute):
    request = {**deb_test_request, "source": "ppa"}
    request.pop("execution_stage")
    response = execute(request)

    assert response.status_code == 200


def test_deb_with_source_and_stage_fails(execute: Execute):
    request = {**deb_test_request, "source": "ppa"}
    response = execute(request)

    assert response.status_code == 422


def test_charm_assigned_to_charm_team_reviewer(db_session: Session, execute: Execute, generator: DataGenerator):
    """Charms should be assigned to reviewers whose teams can review charms"""
    # Create teams with different families
    snap_rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
    charm_rule = generator.gen_artefact_matching_rule(family=FamilyName.charm)
    deb_rule = generator.gen_artefact_matching_rule(family=FamilyName.deb)
    image_rule = generator.gen_artefact_matching_rule(family=FamilyName.image)

    charm_team = generator.gen_team(
        name="charm_reviewers",
        artefact_matching_rules=[charm_rule],
    )
    other_team = generator.gen_team(
        name="other_reviewers",
        artefact_matching_rules=[snap_rule, deb_rule, image_rule],
    )

    # Create users in these teams
    charm_reviewer = generator.gen_user(
        email="charm@example.com",
        teams=[charm_team],
    )
    generator.gen_user(
        email="other@example.com",
        teams=[other_team],
    )

    # Execute a charm test
    response = execute({**charm_test_request, "needs_assignment": True})

    test_execution = db_session.get(TestExecution, response.json()["id"])
    assert test_execution
    assignee = (
        test_execution.artefact_build.artefact.reviewers[0]
        if test_execution.artefact_build.artefact.reviewers
        else None
    )
    assert assignee is not None
    # Check that assignee is in charm_team
    assert any(team.id == charm_team.id for team in assignee.teams)
    assert assignee.id == charm_reviewer.id


def test_snap_assigned_to_snap_team_reviewer(db_session: Session, execute: Execute, generator: DataGenerator):
    """Snaps should be assigned to reviewers whose teams can review snaps"""
    # Create teams with different families
    charm_rule = generator.gen_artefact_matching_rule(family=FamilyName.charm)
    snap_rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
    deb_rule = generator.gen_artefact_matching_rule(family=FamilyName.deb)
    image_rule = generator.gen_artefact_matching_rule(family=FamilyName.image)

    charm_team = generator.gen_team(
        name="charm_reviewers",
        artefact_matching_rules=[charm_rule],
    )
    snap_team = generator.gen_team(
        name="snap_reviewers",
        artefact_matching_rules=[snap_rule, deb_rule, image_rule],
    )

    # Create users in these teams
    generator.gen_user(
        email="charm@example.com",
        teams=[charm_team],
    )
    snap_reviewer = generator.gen_user(
        email="snap@example.com",
        teams=[snap_team],
    )

    # Execute a snap test
    response = execute({**snap_test_request, "needs_assignment": True})

    test_execution = db_session.get(TestExecution, response.json()["id"])
    assert test_execution
    assignee = (
        test_execution.artefact_build.artefact.reviewers[0]
        if test_execution.artefact_build.artefact.reviewers
        else None
    )
    assert assignee is not None
    assert any(team.id == snap_team.id for team in assignee.teams)
    assert assignee.id == snap_reviewer.id


def test_deb_assigned_to_deb_team_reviewer(db_session: Session, execute: Execute, generator: DataGenerator):
    """Debs should be assigned to reviewers whose teams can review debs"""
    # Create teams with different families
    charm_rule = generator.gen_artefact_matching_rule(family=FamilyName.charm)
    snap_rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
    deb_rule = generator.gen_artefact_matching_rule(family=FamilyName.deb)
    image_rule = generator.gen_artefact_matching_rule(family=FamilyName.image)

    charm_team = generator.gen_team(
        name="charm_reviewers",
        artefact_matching_rules=[charm_rule],
    )
    deb_team = generator.gen_team(
        name="deb_reviewers",
        artefact_matching_rules=[deb_rule, snap_rule, image_rule],
    )

    # Create users in these teams
    generator.gen_user(
        email="charm@example.com",
        teams=[charm_team],
    )
    deb_reviewer = generator.gen_user(
        email="deb@example.com",
        teams=[deb_team],
    )

    # Execute a deb test
    response = execute({**deb_test_request, "needs_assignment": True})

    test_execution = db_session.get(TestExecution, response.json()["id"])
    assert test_execution
    assignee = (
        test_execution.artefact_build.artefact.reviewers[0]
        if test_execution.artefact_build.artefact.reviewers
        else None
    )
    assert assignee is not None
    assert any(team.id == deb_team.id for team in assignee.teams)
    assert assignee.id == deb_reviewer.id


def test_image_assigned_to_image_team_reviewer(db_session: Session, execute: Execute, generator: DataGenerator):
    """Images should be assigned to reviewers whose teams can review images"""
    # Create teams with different families
    charm_rule = generator.gen_artefact_matching_rule(family=FamilyName.charm)
    snap_rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
    deb_rule = generator.gen_artefact_matching_rule(family=FamilyName.deb)
    image_rule = generator.gen_artefact_matching_rule(family=FamilyName.image)

    charm_team = generator.gen_team(
        name="charm_reviewers",
        artefact_matching_rules=[charm_rule],
    )
    image_team = generator.gen_team(
        name="image_reviewers",
        artefact_matching_rules=[image_rule, snap_rule, deb_rule],
    )

    # Create users in these teams
    generator.gen_user(
        email="charm@example.com",
        teams=[charm_team],
    )
    image_reviewer = generator.gen_user(
        email="image@example.com",
        teams=[image_team],
    )

    # Execute an image test
    response = execute({**image_test_request, "needs_assignment": True})

    test_execution = db_session.get(TestExecution, response.json()["id"])
    assert test_execution
    assignee = (
        test_execution.artefact_build.artefact.reviewers[0]
        if test_execution.artefact_build.artefact.reviewers
        else None
    )
    assert assignee is not None
    assert any(team.id == image_team.id for team in assignee.teams)
    assert assignee.id == image_reviewer.id


def test_no_ci_link_creates_new_test_execution_each_time(execute: Execute, db_session: Session):
    """
    Test that when ci_link is None/missing, each call creates a NEW test execution
    rather than returning an existing one (which would appear random).
    This prevents the bug where NULL ci_links match all NULL records.
    """
    # First call without ci_link
    request_without_ci_link = snap_test_request.copy()
    request_without_ci_link.pop("ci_link", None)  # Remove ci_link if present

    response1 = execute(request_without_ci_link)
    assert response1.status_code == 200
    te1_id = response1.json()["id"]

    # Second call with same parameters but no ci_link
    response2 = execute(request_without_ci_link)
    assert response2.status_code == 200
    te2_id = response2.json()["id"]

    # Should create TWO different test executions
    assert te1_id != te2_id

    # Both should exist in database
    te1 = db_session.get(TestExecution, te1_id)
    te2 = db_session.get(TestExecution, te2_id)
    assert te1 is not None
    assert te2 is not None
    assert te1.ci_link is None
    assert te2.ci_link is None

    # They should share the same build and environment
    assert te1.artefact_build_id == te2.artefact_build_id
    assert te1.environment_id == te2.environment_id


def test_with_ci_link_reuses_test_execution(execute: Execute):
    """
    Test that when ci_link IS provided, the same test execution is reused
    (the original behavior for non-NULL ci_link).
    """
    # First call with ci_link
    response1 = execute(snap_test_request)
    assert response1.status_code == 200
    te1_id = response1.json()["id"]

    # Second call with same ci_link
    response2 = execute(snap_test_request)
    assert response2.status_code == 200
    te2_id = response2.json()["id"]

    # Should reuse the SAME test execution
    assert te1_id == te2_id


def test_no_assignment_when_no_team_reviewers_available(
    db_session: Session, execute: Execute, generator: DataGenerator
):
    """When no teams can review the family, no assignment should occur"""
    # Create a team that can only review charms
    charm_rule = generator.gen_artefact_matching_rule(family=FamilyName.charm)

    charm_team = generator.gen_team(
        name="charm_reviewers",
        artefact_matching_rules=[charm_rule],
    )
    generator.gen_user(
        email="charm@example.com",
        teams=[charm_team],
    )

    # Execute a snap test (no one can review snaps)
    response = execute({**snap_test_request, "needs_assignment": True})

    test_execution = db_session.get(TestExecution, response.json()["id"])
    assert test_execution
    assignee = (
        test_execution.artefact_build.artefact.reviewers[0]
        if test_execution.artefact_build.artefact.reviewers
        else None
    )
    assert assignee is None


class TestNotifyReviewerAssigned:
    """Tests for notifying new reviewers"""

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch: pytest.MonkeyPatch):
        """Set up Jira environment variables"""
        monkeypatch.setenv("JIRA_CLOUD_ID", "test-cloud-id")
        monkeypatch.setenv("JIRA_EMAIL", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "test-token")

    def test_notify_reviewer_assigned_happy_path(self, generator: DataGenerator, db_session: Session):
        """Test successful creation of notification"""
        # Create artefact with a reviewer and jira issue
        reviewer = generator.gen_user(name="Alice", email="alice@example.com")
        artefact = generator.gen_artefact(
            name="test-snap",
            version="1.0.0",
            reviewers=[reviewer],
        )
        artefact.jira_issue = "TEST-123"
        db_session.commit()

        create_reviewer_notification(
            db_session,
            reviewer,
            artefact,
            NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW,
        )

        # Verify notification was created
        notification = db_session.query(Notification).filter_by(user_id=reviewer.id).first()
        assert notification is not None
        assert notification.notification_type == NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW

    def test_notify_reviewer_assigned_no_jira_issue(self, generator: DataGenerator, db_session: Session):
        """Test that notification is created even without Jira issue (graceful degradation)"""
        # Create artefact with reviewer but NO jira issue
        reviewer = generator.gen_user(name="Alice", email="alice@example.com")
        artefact = generator.gen_artefact(
            name="test-snap",
            version="1.0.0",
            reviewers=[reviewer],
        )  # jira_issue is None by default
        db_session.commit()

        # Should NOT raise - notification should still be created
        create_reviewer_notification(
            db_session,
            reviewer,
            artefact,
            NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW,
        )

        # Verify notification was created
        notification = db_session.query(Notification).filter_by(user_id=reviewer.id).first()
        assert notification is not None
        assert notification.notification_type == NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW
