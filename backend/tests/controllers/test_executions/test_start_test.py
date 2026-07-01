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
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy.orm import Session

from test_observer.common.enums import Permission
from test_observer.controllers.test_executions.start_test import ENVIRONMENTS_PER_REVIEWER, StartTestExecutionController
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
    SolutionStage,
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

solution_test_request = {
    "family": "solution",
    "name": "ubuntu-pro-fips",
    "version": "1.2.3",
    "track": "22.04",
    "source": "ppa:ubuntu-pro/fips",
    "arch": "amd64",
    "execution_stage": SolutionStage.stable,
    "environment": "test-lab",
    "ci_link": "http://localhost",
    "test_plan": "fips test plan",
}


@pytest.mark.parametrize(
    "start_request",
    [snap_test_request, deb_test_request, charm_test_request, image_test_request, solution_test_request],
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
        solution_rule = generator.gen_artefact_matching_rule(family=FamilyName.solution)

        team = generator.gen_team(
            name="reviewers",
            artefact_matching_rules=[snap_rule, deb_rule, charm_rule, image_rule, solution_rule],
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
        solution_rule = generator.gen_artefact_matching_rule(family=FamilyName.solution)
        team = generator.gen_team(
            name="reviewers",
            artefact_matching_rules=[snap_rule, deb_rule, charm_rule, image_rule, solution_rule],
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
        solution_rule = generator.gen_artefact_matching_rule(family=FamilyName.solution)
        team = generator.gen_team(
            name="reviewers",
            artefact_matching_rules=[snap_rule, deb_rule, charm_rule, image_rule, solution_rule],
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
        solution_rule = generator.gen_artefact_matching_rule(family=FamilyName.solution)
        team = generator.gen_team(
            name="reviewers",
            artefact_matching_rules=[snap_rule, deb_rule, charm_rule, image_rule, solution_rule],
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
        if start_request["family"] == "image":
            pytest.skip("an image is single-architecture, so it cannot have multiple builds")

        # Create a team that can review all families
        snap_rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
        deb_rule = generator.gen_artefact_matching_rule(family=FamilyName.deb)
        charm_rule = generator.gen_artefact_matching_rule(family=FamilyName.charm)
        image_rule = generator.gen_artefact_matching_rule(family=FamilyName.image)
        solution_rule = generator.gen_artefact_matching_rule(family=FamilyName.solution)
        team = generator.gen_team(
            name="reviewers",
            artefact_matching_rules=[snap_rule, deb_rule, charm_rule, image_rule, solution_rule],
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
        solution_rule = generator.gen_artefact_matching_rule(family=FamilyName.solution)
        team = generator.gen_team(
            name="reviewers",
            artefact_matching_rules=[snap_rule, deb_rule, charm_rule, image_rule, solution_rule],
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
        """When starting test with needs_assignment=true, a single combined artefact-review
        notification should be created per assigned reviewer, and no environment notifications."""
        # Create a team with matching rules for all families
        snap_rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
        deb_rule = generator.gen_artefact_matching_rule(family=FamilyName.deb)
        charm_rule = generator.gen_artefact_matching_rule(family=FamilyName.charm)
        image_rule = generator.gen_artefact_matching_rule(family=FamilyName.image)
        solution_rule = generator.gen_artefact_matching_rule(family=FamilyName.solution)

        team = generator.gen_team(
            name="reviewers",
            artefact_matching_rules=[snap_rule, deb_rule, charm_rule, image_rule, solution_rule],
        )
        # Create users on the team
        generator.gen_user(email="reviewer1@example.com", teams=[team])
        generator.gen_user(email="reviewer2@example.com", teams=[team])

        # Execute test with automatic assignment
        response = execute({**start_request, "needs_assignment": True})

        test_execution = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        assert len(test_execution.artefact_build.artefact.reviewers) > 0

        # Each assigned reviewer gets exactly one artefact-review notification
        assigned_reviewer_ids = [r.id for r in test_execution.artefact_build.artefact.reviewers]
        artefact_notifications = (
            self._db_session.query(Notification)
            .filter(
                Notification.user_id.in_(assigned_reviewer_ids),
                Notification.notification_type == NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW,
            )
            .all()
        )
        assert len(artefact_notifications) == len(assigned_reviewer_ids)

        # No environment-review notifications are created anymore
        env_notifications = (
            self._db_session.query(Notification)
            .filter(
                Notification.user_id.in_(assigned_reviewer_ids),
                Notification.notification_type == NotificationType.USER_ASSIGNED_ENVIRONMENT_REVIEW,
            )
            .all()
        )
        assert len(env_notifications) == 0

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

    def test_reviewer_gets_single_artefact_notification_no_environment_notification(
        self, execute: Execute, generator: DataGenerator, start_request: dict[str, Any]
    ):
        """A reviewer newly assigned to an artefact receives a single artefact-review
        notification and no separate environment-review notification."""
        snap_rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
        deb_rule = generator.gen_artefact_matching_rule(family=FamilyName.deb)
        charm_rule = generator.gen_artefact_matching_rule(family=FamilyName.charm)
        image_rule = generator.gen_artefact_matching_rule(family=FamilyName.image)
        solution_rule = generator.gen_artefact_matching_rule(family=FamilyName.solution)

        team = generator.gen_team(
            name="reviewers",
            artefact_matching_rules=[snap_rule, deb_rule, charm_rule, image_rule, solution_rule],
        )
        reviewer = generator.gen_user(email="reviewer@example.com", teams=[team])

        response = execute({**start_request, "needs_assignment": True})

        test_execution = self._db_session.get(TestExecution, response.json()["id"])
        assert test_execution
        assert reviewer in test_execution.artefact_build.artefact.reviewers

        notifications = self._db_session.query(Notification).filter(Notification.user_id == reviewer.id).all()

        notification_types = [n.notification_type for n in notifications]
        assert notification_types == [NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW]
        assert NotificationType.USER_ASSIGNED_ENVIRONMENT_REVIEW not in notification_types

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
        assert artefact.source == request.get("source", "")


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
        "sha256",
        "environment",
        "test_plan",
    ],
)
def test_image_schema_required_fields(execute: Execute, field: str):
    """Fields that are always required by the request schema for images."""
    request = image_test_request.copy()
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
        "owner",
        "image_url",
        "execution_stage",
    ],
)
def test_image_missing_create_fields_returns_422(execute: Execute, field: str):
    """When no image with the sha256 exists yet, creating one requires all these
    fields. Omitting any returns a clean 422 (not a 500)."""
    request = image_test_request.copy()
    request.pop(field)
    response = execute(request)

    assert response.status_code == 422


# A second, distinct sha256 used for tests that pre-seed an existing image so that the
# request under test resolves to "existing" rather than "create".
_EXISTING_IMAGE_SHA256 = "a" * 64


def _existing_image_request(**overrides: object) -> dict[str, Any]:
    """A minimal image start-test payload for an image that already exists: just the
    sha256 plus the test-execution context, no descriptive fields and no arch."""
    request: dict[str, Any] = {
        "family": "image",
        "sha256": _EXISTING_IMAGE_SHA256,
        "environment": "xps",
        "test_plan": "image test plan",
        "ci_link": "http://localhost",
    }
    request.update(overrides)
    return request


def test_image_minimal_payload_reuses_existing_artefact(
    execute: Execute, generator: DataGenerator, db_session: Session
):
    """An existing image can be tested with only its sha256 + test context; arch is
    derived from the image's single build."""
    image = generator.gen_image(sha256=_EXISTING_IMAGE_SHA256, name="noble-desktop-arm64")
    generator.gen_artefact_build(image, architecture="arm64")

    response = execute(_existing_image_request())

    assert response.status_code == 200
    test_execution = db_session.get(TestExecution, response.json()["id"])
    assert test_execution is not None
    assert test_execution.artefact_build.artefact_id == image.id
    # arch was omitted and derived from the existing build
    assert test_execution.artefact_build.architecture == "arm64"
    assert test_execution.environment.architecture == "arm64"


def test_image_conflicting_arch_is_rejected(execute: Execute, generator: DataGenerator):
    """A provided arch that differs from the existing image's build is rejected (422)."""
    image = generator.gen_image(sha256=_EXISTING_IMAGE_SHA256)
    generator.gen_artefact_build(image, architecture="amd64")

    response = execute(_existing_image_request(arch="arm64"))

    assert response.status_code == 422


def test_image_same_sha_reuses_existing_artefact(execute: Execute, db_session: Session):
    """Regression: two image payloads sharing a sha256 used to 500 via an uncaught
    NoResultFound. The sha256 identifies the image, so the second request now reuses
    the existing artefact."""
    first = {**image_test_request, "sha256": _EXISTING_IMAGE_SHA256}
    first_response = execute(first)
    assert first_response.status_code == 200
    first_te = db_session.get(TestExecution, first_response.json()["id"])
    assert first_te is not None

    second = {
        **image_test_request,
        "sha256": _EXISTING_IMAGE_SHA256,
        "name": "different-image",
        "ci_link": "http://localhost/other",
    }
    second_response = execute(second)
    assert second_response.status_code == 200
    second_te = db_session.get(TestExecution, second_response.json()["id"])
    assert second_te is not None

    assert first_te.artefact_build.artefact_id == second_te.artefact_build.artefact_id


@pytest.mark.parametrize(
    "field",
    [
        "name",
        "version",
        "track",
        "source",
        "arch",
        "execution_stage",
        "environment",
        "test_plan",
    ],
)
def test_solution_required_fields(execute: Execute, field: str):
    request = solution_test_request.copy()
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


@pytest.mark.parametrize(
    "invalid_stage",
    set(StageName) - set(SolutionStage),
)
def test_validates_stage_for_solutions(execute: Execute, invalid_stage: StageName):
    response = execute({**solution_test_request, "execution_stage": invalid_stage})

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


def test_solution_includes_track_source_and_stage(execute: Execute, db_session: Session):
    """Verify that a solution test execution creates an artefact with track, source, and stage."""
    response = execute(solution_test_request)
    assert response.status_code == 200

    test_execution = db_session.get(TestExecution, response.json()["id"])
    assert test_execution

    artefact = test_execution.artefact_build.artefact
    assert artefact.name == solution_test_request["name"]
    assert artefact.version == solution_test_request["version"]
    assert artefact.track == solution_test_request["track"]
    assert artefact.source == solution_test_request["source"]
    assert artefact.stage == solution_test_request["execution_stage"]
    assert artefact.family == FamilyName.solution


def test_solution_track_source_stage_are_part_of_uniqueness(execute: Execute, db_session: Session):
    """Verify that changing track, source, or stage creates a different artefact."""
    response = execute(solution_test_request)
    te1 = db_session.get(TestExecution, response.json()["id"])

    # Different track should create a new artefact
    request_different_track = {
        **solution_test_request,
        "track": "24.04",
        "ci_link": "http://localhost/1",
    }
    response = execute(request_different_track)
    te2 = db_session.get(TestExecution, response.json()["id"])

    assert te1 and te2
    assert te1.artefact_build.artefact_id != te2.artefact_build.artefact_id

    # Different source should create a new artefact
    request_different_source = {
        **solution_test_request,
        "source": "ppa:ubuntu-pro/other",
        "ci_link": "http://localhost/2",
    }
    response = execute(request_different_source)
    te3 = db_session.get(TestExecution, response.json()["id"])

    assert te1 and te3
    assert te1.artefact_build.artefact_id != te3.artefact_build.artefact_id

    # Different stage should create a new artefact
    request_different_stage = {
        **solution_test_request,
        "execution_stage": "beta",
        "ci_link": "http://localhost/3",
    }
    response = execute(request_different_stage)
    te4 = db_session.get(TestExecution, response.json()["id"])

    assert te1 and te4
    assert te1.artefact_build.artefact_id != te4.artefact_build.artefact_id


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


def test_due_date_not_updated_when_no_new_reviewers_assigned(
    db_session: Session, execute: Execute, generator: DataGenerator
):
    """due_date must not be updated when needs_assignment=True but number_of_reviewers_to_assign
    is 0 (artefact already has enough reviewers for the current environment count).
    Two eligible users exist so the users query is non-empty, but the artefact already has
    one reviewer which is sufficient for < ENVIRONMENTS_PER_REVIEWER environments.
    determine_due_date must not be called a second time.
    """
    # GIVEN two eligible reviewers (so `users` is non-empty on the second call too)
    rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
    team = generator.gen_team(artefact_matching_rules=[rule])
    generator.gen_user(email="reviewer1@example.com", teams=[team])
    generator.gen_user(email="reviewer2@example.com", teams=[team])

    # AND the artefact already has a reviewer and a due_date from the first call
    first_response = execute({**snap_test_request, "needs_assignment": True})
    assert first_response.status_code == 200

    # WHEN a second environment is added (still well below ENVIRONMENTS_PER_REVIEWER,
    # so number_of_reviewers_to_assign remains 0), with determine_due_date patched
    # to a sentinel so any unwanted call would produce a detectable value
    db_session.expire_all()
    sentinel_date = date(2099, 1, 1)
    with patch.object(StartTestExecutionController, "determine_due_date", return_value=sentinel_date):
        execute(
            {**snap_test_request, "environment": "env-2", "ci_link": "http://localhost/2", "needs_assignment": True}
        )

    # THEN the due_date was NOT updated to the sentinel (determine_due_date was not called)
    test_execution = db_session.get(TestExecution, first_response.json()["id"])
    assert test_execution is not None
    artefact = test_execution.artefact_build.artefact
    assert artefact.due_date != sentinel_date, "due_date must not be updated when no new reviewers are assigned"


def test_first_environment_gets_reviewer_assigned_to_env_review(
    db_session: Session, execute: Execute, generator: DataGenerator
):
    """When the first environment is created, its environment review gets a reviewer assigned."""
    # GIVEN a user in a team with a matching rule for snaps
    rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
    team = generator.gen_team(artefact_matching_rules=[rule])
    reviewer = generator.gen_user(teams=[team])

    # WHEN a single test execution is started with needs_assignment=True
    response = execute({**snap_test_request, "needs_assignment": True})

    # THEN the artefact has the reviewer assigned
    test_execution = db_session.get(TestExecution, response.json()["id"])
    assert test_execution is not None
    artefact = test_execution.artefact_build.artefact
    assert artefact.reviewers == [reviewer]

    # AND the single environment review also has the reviewer assigned
    env_review = test_execution.artefact_build.environment_reviews[0]
    assert env_review.reviewers == [reviewer]


def test_subsequent_environments_also_get_reviewer_assigned_to_env_review(
    db_session: Session, execute: Execute, generator: DataGenerator
):
    """When environments 2–49 are created, their environment reviews also get a reviewer assigned."""
    # GIVEN a user in a team with a matching rule for snaps
    rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
    team = generator.gen_team(artefact_matching_rules=[rule])
    generator.gen_user(teams=[team])

    # WHEN 5 environments are created one by one, each with needs_assignment=True
    last_response = None
    for i in range(5):
        db_session.expire_all()  # simulate a fresh session per request
        last_response = execute(
            {
                **snap_test_request,
                "environment": f"env-{i}",
                "ci_link": f"http://localhost/{i}",
                "needs_assignment": True,
            }
        )
        assert last_response.status_code == 200

    assert last_response is not None
    test_execution = db_session.get(TestExecution, last_response.json()["id"])
    assert test_execution is not None
    artefact = test_execution.artefact_build.artefact

    # THEN the artefact still has exactly 1 reviewer
    assert len(artefact.reviewers) == 1

    # AND every environment review has that reviewer assigned
    for build in artefact.builds:
        for env_review in build.environment_reviews:
            assert len(env_review.reviewers) == 1, (
                f"Environment review {env_review.id} should have exactly 1 reviewer assigned"
            )


def test_exceeding_50_environments_adds_new_artefact_reviewer(
    db_session: Session, execute: Execute, generator: DataGenerator
):
    """When an artefact accumulates more than ENVIRONMENTS_PER_REVIEWER environments,
    a second reviewer is assigned."""
    # GIVEN two users in a team with a matching rule for snaps
    rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
    team = generator.gen_team(artefact_matching_rules=[rule])
    generator.gen_user(email="reviewer1@example.com", teams=[team])
    generator.gen_user(email="reviewer2@example.com", teams=[team])

    # WHEN ENVIRONMENTS_PER_REVIEWER + 2 environments are created one by one, each with needs_assignment=True
    last_response = None
    for i in range(ENVIRONMENTS_PER_REVIEWER + 2):
        db_session.expire_all()  # simulate a fresh session per request
        last_response = execute(
            {
                **snap_test_request,
                "environment": f"env-{i}",
                "ci_link": f"http://localhost/{i}",
                "needs_assignment": True,
            }
        )
        assert last_response.status_code == 200

    assert last_response is not None
    test_execution = db_session.get(TestExecution, last_response.json()["id"])
    assert test_execution is not None
    artefact = test_execution.artefact_build.artefact

    # THEN the artefact has 2 reviewers (ceil((ENVIRONMENTS_PER_REVIEWER + 2) / ENVIRONMENTS_PER_REVIEWER) = 2)
    assert len(artefact.reviewers) == 2

    # AND every environment review has exactly one reviewer assigned
    for build in artefact.builds:
        for env_review in build.environment_reviews:
            assert len(env_review.reviewers) == 1, (
                f"Environment review {env_review.id} should have exactly 1 reviewer assigned"
            )


def test_repeated_call_for_same_environment_does_not_duplicate_notifications(
    db_session: Session, execute: Execute, generator: DataGenerator
):
    """Calling start_test twice with the same ci_link (same env_review) must not create
    duplicate notifications. get_or_create reuses the ArtefactBuildEnvironmentReview, and
    _assign_reviewers_to_environments skips it because it already has a reviewer assigned.
    """
    # GIVEN a reviewer with a matching rule
    rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
    team = generator.gen_team(artefact_matching_rules=[rule])
    reviewer = generator.gen_user(teams=[team])

    # WHEN the first call creates the assignment
    execute({**snap_test_request, "needs_assignment": True})
    notification_count_after_first = db_session.query(Notification).filter(Notification.user_id == reviewer.id).count()

    # WHEN the same request is repeated (same ci_link → same test_execution and env_review)
    db_session.expire_all()  # simulate a fresh session per request
    execute({**snap_test_request, "needs_assignment": True})

    # THEN no new notifications are created
    notification_count_after_second = db_session.query(Notification).filter(Notification.user_id == reviewer.id).count()
    assert notification_count_after_second == notification_count_after_first


def test_environment_created_without_assignment_gets_reviewer_on_next_assignment_call(
    db_session: Session, execute: Execute, generator: DataGenerator
):
    """An env_review created with needs_assignment=False (no reviewer assigned) is picked up
    and assigned on the next call with needs_assignment=True for the same artefact.
    _assign_reviewers_to_environments scans all unassigned env_reviews, not just the
    current one, so the gap is healed automatically.
    """
    # GIVEN a reviewer with a matching rule
    rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
    team = generator.gen_team(artefact_matching_rules=[rule])
    generator.gen_user(teams=[team])

    # WHEN env-0 is created with assignment (reviewer assigned to env-0 review)
    execute({**snap_test_request, "environment": "env-0", "ci_link": "http://localhost/0", "needs_assignment": True})
    # WHEN env-1 is created without assignment (env-1 review has no reviewer)
    db_session.expire_all()
    execute({**snap_test_request, "environment": "env-1", "ci_link": "http://localhost/1", "needs_assignment": False})
    # WHEN env-2 is created with assignment
    db_session.expire_all()
    response = execute(
        {**snap_test_request, "environment": "env-2", "ci_link": "http://localhost/2", "needs_assignment": True}
    )

    # THEN all three env_reviews have a reviewer assigned — including env-1 which was skipped
    test_execution = db_session.get(TestExecution, response.json()["id"])
    assert test_execution is not None
    artefact = test_execution.artefact_build.artefact
    for build in artefact.builds:
        for env_review in build.environment_reviews:
            assert len(env_review.reviewers) == 1, (
                f"Environment review {env_review.id} (env {env_review.environment.name}) "
                "should have exactly 1 reviewer assigned"
            )


def test_reviewer_gets_at_most_one_artefact_jira_card(db_session: Session, execute: Execute, generator: DataGenerator):
    """A reviewer must receive exactly one artefact-review Jira card per artefact,
    regardless of how many environments are added afterwards.

    The reviewer is only in newly_assigned_reviewers on the first call (subsequent calls
    filter them out via .not_in()), so USER_ASSIGNED_ARTEFACT_REVIEW only appears in
    the BatchReviewerAssignedMessage once.
    """
    # GIVEN a reviewer with a matching rule
    rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
    team = generator.gen_team(artefact_matching_rules=[rule])
    generator.gen_user(teams=[team])

    # Pre-create the artefact (without assignment) so we can set jira_issue before
    # any Jira card logic runs
    response = execute({**snap_test_request, "needs_assignment": False})
    test_execution = db_session.get(TestExecution, response.json()["id"])
    assert test_execution is not None
    artefact = test_execution.artefact_build.artefact
    artefact.jira_issue = "PROJ-123"
    db_session.commit()

    # WHEN 5 environments are created one by one with needs_assignment=True,
    # intercepting all Jira card creation
    with patch(
        "test_observer.controllers.test_executions.start_test.batch_create_jira_reviewer_cards"
    ) as mock_create_cards:
        for i in range(5):
            db_session.expire_all()  # simulate a fresh session per request
            execute(
                {
                    **snap_test_request,
                    "environment": f"env-{i}",
                    "ci_link": f"http://localhost/{i}",
                    "needs_assignment": True,
                }
            )

    # THEN USER_ASSIGNED_ARTEFACT_REVIEW appears exactly once across all Jira calls
    artefact_card_count = sum(
        1
        for call in mock_create_cards.call_args_list
        for _reviewer, notif_types in call.args[0].assigned_reviews
        if NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW in notif_types
    )
    assert artefact_card_count == 1, f"Expected 1 artefact review Jira card, got {artefact_card_count}"


def test_no_environment_jira_cards_are_created(db_session: Session, execute: Execute, generator: DataGenerator):
    """Environment-review Jira cards are no longer created, regardless of how many
    environments are added.
    """
    # GIVEN a reviewer with a matching rule
    rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
    team = generator.gen_team(artefact_matching_rules=[rule])
    generator.gen_user(teams=[team])

    # Pre-create the artefact so we can set jira_issue before any Jira card logic runs
    response = execute({**snap_test_request, "needs_assignment": False})
    test_execution = db_session.get(TestExecution, response.json()["id"])
    assert test_execution is not None
    artefact = test_execution.artefact_build.artefact
    artefact.jira_issue = "PROJ-123"
    db_session.commit()

    # WHEN 5 environments are created one by one with needs_assignment=True,
    # intercepting all Jira card creation
    with patch(
        "test_observer.controllers.test_executions.start_test.batch_create_jira_reviewer_cards"
    ) as mock_create_cards:
        for i in range(5):
            db_session.expire_all()  # simulate a fresh session per request
            execute(
                {
                    **snap_test_request,
                    "environment": f"env-{i}",
                    "ci_link": f"http://localhost/{i}",
                    "needs_assignment": True,
                }
            )

    # THEN no USER_ASSIGNED_ENVIRONMENT_REVIEW card is ever created
    env_card_count = sum(
        1
        for call in mock_create_cards.call_args_list
        for _reviewer, notif_types in call.args[0].assigned_reviews
        if NotificationType.USER_ASSIGNED_ENVIRONMENT_REVIEW in notif_types
    )
    assert env_card_count == 0, f"Expected 0 environment review Jira cards, got {env_card_count}"


def test_reviewer_gets_single_combined_jira_card(db_session: Session, execute: Execute, generator: DataGenerator):
    """A reviewer newly assigned to an artefact receives a single combined Jira card
    (USER_ASSIGNED_ARTEFACT_REVIEW) and no separate environment card."""
    # GIVEN a reviewer with a matching rule
    rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
    team = generator.gen_team(artefact_matching_rules=[rule])
    reviewer = generator.gen_user(teams=[team])

    # Pre-create the artefact so we can set jira_issue before the assignment call
    response = execute({**snap_test_request, "needs_assignment": False})
    test_execution = db_session.get(TestExecution, response.json()["id"])
    assert test_execution is not None
    artefact = test_execution.artefact_build.artefact
    artefact.jira_issue = "PROJ-123"
    db_session.commit()

    # WHEN the first assignment call runs (reviewer gets assigned to artefact + env review)
    with patch(
        "test_observer.controllers.test_executions.start_test.batch_create_jira_reviewer_cards"
    ) as mock_create_cards:
        db_session.expire_all()
        execute({**snap_test_request, "needs_assignment": True})

    # THEN the reviewer gets exactly one card, of the artefact-review type, and no env card
    mock_create_cards.assert_called_once()
    message = mock_create_cards.call_args[0][0]
    reviewer_card_types = [t for r, types in message.assigned_reviews if r.id == reviewer.id for t in types]

    assert reviewer_card_types == [NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW]
    assert NotificationType.USER_ASSIGNED_ENVIRONMENT_REVIEW not in reviewer_card_types


def test_no_new_jira_cards_when_existing_reviewer_assigned_to_new_environment(
    db_session: Session, execute: Execute, generator: DataGenerator
):
    """When a reviewer already assigned to an artefact is assigned to a new environment review,
    no new Jira cards should be created — cards are only created when new artefact reviewers
    are assigned, not when existing reviewers pick up additional environments."""
    # GIVEN a reviewer with a matching rule and an artefact with jira_issue
    rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
    team = generator.gen_team(artefact_matching_rules=[rule])
    generator.gen_user(teams=[team])

    response = execute({**snap_test_request, "needs_assignment": False})
    test_execution = db_session.get(TestExecution, response.json()["id"])
    assert test_execution is not None
    test_execution.artefact_build.artefact.jira_issue = "PROJ-123"
    db_session.commit()

    # WHEN the first call assigns the reviewer (to artefact + env-0)
    with patch("test_observer.controllers.test_executions.start_test.batch_create_jira_reviewer_cards"):
        db_session.expire_all()
        execute({**snap_test_request, "needs_assignment": True})

    # WHEN a second environment is added, assigning the same reviewer to env-1
    with patch(
        "test_observer.controllers.test_executions.start_test.batch_create_jira_reviewer_cards"
    ) as mock_second_call:
        db_session.expire_all()
        execute(
            {**snap_test_request, "environment": "env-1", "ci_link": "http://localhost/1", "needs_assignment": True}
        )

    # THEN no new Jira cards are created on the second call
    mock_second_call.assert_not_called()


def test_existing_reviewer_gets_no_notification_for_new_environment(
    db_session: Session, execute: Execute, generator: DataGenerator
):
    """When a reviewer already assigned to an artefact is assigned to a new environment review,
    they should NOT receive any new notification — per-environment notifications no longer exist."""
    # GIVEN a reviewer with a matching rule
    rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
    team = generator.gen_team(artefact_matching_rules=[rule])
    reviewer = generator.gen_user(teams=[team])

    # WHEN the first call assigns the reviewer (to artefact + env-0)
    execute({**snap_test_request, "needs_assignment": True})
    notifications_after_first = db_session.query(Notification).filter(Notification.user_id == reviewer.id).count()

    # WHEN a second environment is added
    db_session.expire_all()
    execute({**snap_test_request, "environment": "env-1", "ci_link": "http://localhost/1", "needs_assignment": True})

    # THEN the reviewer has no new notifications
    notifications_after_second = db_session.query(Notification).filter(Notification.user_id == reviewer.id).count()
    assert notifications_after_second == notifications_after_first


def test_reviewer_gets_single_notification_regardless_of_environment_count(
    db_session: Session, execute: Execute, generator: DataGenerator
):
    """A reviewer newly assigned to an artefact receives exactly one notification,
    regardless of how many environments the artefact accumulates.
    """
    # GIVEN a reviewer with a matching rule
    rule = generator.gen_artefact_matching_rule(family=FamilyName.snap)
    team = generator.gen_team(artefact_matching_rules=[rule])
    reviewer = generator.gen_user(teams=[team])

    # WHEN 3 environments are created one by one, each with needs_assignment=True
    for i in range(3):
        db_session.expire_all()  # simulate a fresh session per request
        response = execute(
            {
                **snap_test_request,
                "environment": f"env-{i}",
                "ci_link": f"http://localhost/{i}",
                "needs_assignment": True,
            }
        )
        assert response.status_code == 200

    # THEN the reviewer has exactly one notification, of the artefact-review type
    notifications = db_session.query(Notification).filter(Notification.user_id == reviewer.id).all()
    assert [n.notification_type for n in notifications] == [NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW]


def test_manually_assigned_reviewer_gets_env_review_assigned_on_new_environment(
    db_session: Session, execute: Execute, generator: DataGenerator
):
    """When a reviewer is assigned to an artefact manually (no matching rule), new environment
    reviews created with needs_assignment=True must still be assigned to that reviewer.
    _assign_reviewers_to_environments() must run even when rule_ids is empty.
    """
    # GIVEN a reviewer assigned directly to the artefact (no team/matching rule)
    reviewer = generator.gen_user()
    generator.gen_artefact(
        name=snap_test_request["name"],  # type: ignore[arg-type]
        version=snap_test_request["version"],  # type: ignore[arg-type]
        family=FamilyName.snap,
        track=snap_test_request["track"],  # type: ignore[arg-type]
        store=snap_test_request["store"],  # type: ignore[arg-type]
        stage=snap_test_request["execution_stage"],  # type: ignore[arg-type]
        reviewers=[reviewer],
    )
    db_session.flush()

    # WHEN a test execution is started with needs_assignment=True
    db_session.expire_all()
    response = execute({**snap_test_request, "needs_assignment": True})
    assert response.status_code == 200

    # THEN the environment review has the reviewer assigned
    test_execution = db_session.get(TestExecution, response.json()["id"])
    assert test_execution is not None
    env_review = test_execution.artefact_build.environment_reviews[0]
    assert env_review.reviewers == [reviewer], "Manually-assigned reviewer should be assigned to the environment review"


def test_manually_assigned_reviewer_gets_no_notification_on_new_environment(
    db_session: Session, execute: Execute, generator: DataGenerator
):
    """A reviewer manually pre-assigned to an artefact is not a newly assigned reviewer,
    so starting a test execution for a new environment creates no notification for them
    (per-environment notifications no longer exist).
    """
    # GIVEN a reviewer assigned directly to the artefact (no team/matching rule)
    reviewer = generator.gen_user()
    generator.gen_artefact(
        name=snap_test_request["name"],  # type: ignore[arg-type]
        version=snap_test_request["version"],  # type: ignore[arg-type]
        family=FamilyName.snap,
        track=snap_test_request["track"],  # type: ignore[arg-type]
        store=snap_test_request["store"],  # type: ignore[arg-type]
        stage=snap_test_request["execution_stage"],  # type: ignore[arg-type]
        reviewers=[reviewer],
    )
    db_session.flush()

    # WHEN a test execution is started with needs_assignment=True
    db_session.expire_all()
    response = execute({**snap_test_request, "needs_assignment": True})
    assert response.status_code == 200

    # THEN the reviewer receives no notification
    notification_count = db_session.query(Notification).filter(Notification.user_id == reviewer.id).count()
    assert notification_count == 0, (
        f"Manually pre-assigned reviewer should receive no notification, got {notification_count}"
    )


class TestAssignReviewersToEnvironments:
    """Tests for _assign_reviewers_to_environments method"""

    def test_assign_reviewers_to_environments_no_duplicates(self, generator: DataGenerator, db_session: Session):
        """Test that _assign_reviewers_to_environments returns reviewers without duplicates"""
        # GIVEN an artefact with multiple reviewers, builds and environment reviews
        reviewer1 = generator.gen_user(name="Alice", email="alice@example.com")
        reviewer2 = generator.gen_user(name="Bob", email="bob@example.com")
        reviewer3 = generator.gen_user(name="Charlie", email="charlie@example.com")

        artefact = generator.gen_artefact(
            name="test-snap",
            version="1.0.0",
            reviewers=[reviewer1, reviewer2, reviewer3],
        )

        build1 = generator.gen_artefact_build(artefact=artefact, architecture="amd64")
        build2 = generator.gen_artefact_build(artefact=artefact, architecture="arm64")

        # GIVEN environment reviews without reviewers assigned
        env1 = generator.gen_environment(name="env1")
        env2 = generator.gen_environment(name="env2")
        env3 = generator.gen_environment(name="env3")

        generator.gen_artefact_build_environment_review(artefact_build=build1, environment=env1, reviewers=[])
        generator.gen_artefact_build_environment_review(artefact_build=build1, environment=env2, reviewers=[])
        generator.gen_artefact_build_environment_review(artefact_build=build2, environment=env1, reviewers=[])
        generator.gen_artefact_build_environment_review(artefact_build=build2, environment=env2, reviewers=[])
        generator.gen_artefact_build_environment_review(artefact_build=build2, environment=env3, reviewers=[])

        db_session.commit()

        # WHEN _assign_reviewers_to_environments is called
        controller = StartTestExecutionController.__new__(StartTestExecutionController)
        controller.db = db_session
        controller.artefact = artefact

        newly_assigned_reviewers = controller._assign_reviewers_to_environments()

        # THEN the returned list has no duplicates
        assert len(newly_assigned_reviewers) == len(set(newly_assigned_reviewers)), (
            f"Duplicate reviewers found in result. "
            f"Length: {len(newly_assigned_reviewers)}, Unique: {len(set(newly_assigned_reviewers))}"
        )
