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
from datetime import date, timedelta

from sqlalchemy.orm import Session

from fastapi.testclient import TestClient

from test_observer.data_access.models import TestExecution
from test_observer.data_access.models_enums import (
    ArtefactStatus,
    TestExecutionReviewDecision,
)
from tests.data_generator import DataGenerator


def test_get_latest_artefacts_by_family(
    generator: DataGenerator, test_client: TestClient
):
    """Should only get latest artefacts and only ones that belong to given family"""
    relevant_artefact = generator.gen_artefact(
        "edge",
        version="2",
        status=ArtefactStatus.MARKED_AS_FAILED,
    )

    old_timestamp = relevant_artefact.created_at - timedelta(days=1)
    generator.gen_artefact("edge", created_at=old_timestamp, version="1")
    generator.gen_artefact("proposed")

    response = test_client.get("/v1/artefacts", params={"family": "snap"})

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": relevant_artefact.id,
            "name": relevant_artefact.name,
            "version": relevant_artefact.version,
            "track": relevant_artefact.track,
            "store": relevant_artefact.store,
            "series": relevant_artefact.series,
            "repo": relevant_artefact.repo,
            "stage": relevant_artefact.stage.name,
            "status": relevant_artefact.status,
            "assignee": None,
            "due_date": (
                relevant_artefact.due_date.strftime("%Y-%m-%d")
                if relevant_artefact.due_date
                else None
            ),
            "bug_link": "",
            "all_test_executions_count": 0,
            "completed_test_executions_count": 0,
        }
    ]


def test_get_artefact(test_client: TestClient, generator: DataGenerator):
    """Should be able to fetch an existing artefact"""
    u = generator.gen_user()
    a = generator.gen_artefact(
        "edge",
        status=ArtefactStatus.APPROVED,
        bug_link="localhost/bug",
        due_date=date(2024, 12, 24),
        assignee_id=u.id,
    )

    response = test_client.get(f"/v1/artefacts/{a.id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": a.id,
        "name": a.name,
        "version": a.version,
        "track": a.track,
        "store": a.store,
        "series": a.series,
        "repo": a.repo,
        "stage": a.stage.name,
        "status": a.status,
        "assignee": {
            "id": u.id,
            "launchpad_handle": u.launchpad_handle,
            "launchpad_email": u.launchpad_email,
            "name": u.name,
        },
        "due_date": "2024-12-24",
        "bug_link": a.bug_link,
        "all_test_executions_count": 0,
        "completed_test_executions_count": 0,
    }


def test_get_artefact_test_execution_counts(
    test_client: TestClient,
    generator: DataGenerator,
    db_session: Session,
):
    u = generator.gen_user()
    a = generator.gen_artefact(
        "edge",
        status=ArtefactStatus.APPROVED,
        bug_link="localhost/bug",
        due_date=date(2024, 12, 24),
        assignee_id=u.id,
    )
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment()
    te = generator.gen_test_execution(ab, e)

    # Verify completed test execution count is zero, it is not reviewed yet
    response = test_client.get(f"/v1/artefacts/{a.id}")
    assert response.status_code == 200
    assert response.json()["all_test_executions_count"] == 1
    assert response.json()["completed_test_executions_count"] == 0

    te.review_decision = [TestExecutionReviewDecision.APPROVED_ALL_TESTS_PASS]
    db_session.commit()
    db_session.refresh(te)

    # Verify completed test execution count is one, it is reviewed
    response = test_client.get(f"/v1/artefacts/{a.id}")
    assert response.status_code == 200
    assert response.json()["all_test_executions_count"] == 1
    assert response.json()["completed_test_executions_count"] == 1


def test_get_artefact_builds(test_client: TestClient, generator: DataGenerator):
    a = generator.gen_artefact("beta")
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment()
    te = generator.gen_test_execution(ab, e)

    response = test_client.get(f"/v1/artefacts/{a.id}/builds")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": ab.id,
            "revision": ab.revision,
            "architecture": ab.architecture,
            "test_executions": [
                {
                    "id": te.id,
                    "ci_link": te.ci_link,
                    "c3_link": te.c3_link,
                    "status": te.status.value,
                    "environment": {
                        "id": e.id,
                        "name": e.name,
                        "architecture": e.architecture,
                    },
                    "review_decision": [],
                    "review_comment": "",
                    "is_rerun_requested": False,
                }
            ],
        }
    ]


def test_get_artefact_builds_sorts_test_executions_by_environment_name(
    test_client: TestClient, generator: DataGenerator
):
    a = generator.gen_artefact("beta")
    ab = generator.gen_artefact_build(a)
    e2 = generator.gen_environment("e2")
    e1 = generator.gen_environment("e1")
    te2 = generator.gen_test_execution(ab, e2)
    te1 = generator.gen_test_execution(ab, e1)

    assert test_client.get(f"/v1/artefacts/{a.id}/builds").json() == [
        {
            "id": ab.id,
            "revision": ab.revision,
            "architecture": ab.architecture,
            "test_executions": [
                {
                    "id": te1.id,
                    "ci_link": te1.ci_link,
                    "c3_link": te1.c3_link,
                    "status": te1.status.value,
                    "environment": {
                        "id": e1.id,
                        "name": e1.name,
                        "architecture": e1.architecture,
                    },
                    "review_decision": [],
                    "review_comment": "",
                    "is_rerun_requested": False,
                },
                {
                    "id": te2.id,
                    "ci_link": te2.ci_link,
                    "c3_link": te2.c3_link,
                    "status": te2.status.value,
                    "environment": {
                        "id": e2.id,
                        "name": e2.name,
                        "architecture": e2.architecture,
                    },
                    "review_decision": [],
                    "review_comment": "",
                    "is_rerun_requested": False,
                },
            ],
        }
    ]


def test_get_artefact_builds_only_latest(
    test_client: TestClient, generator: DataGenerator
):
    artefact = generator.gen_artefact("beta")
    generator.gen_artefact_build(artefact=artefact, revision=1)
    artefact_build2 = generator.gen_artefact_build(artefact=artefact, revision=2)

    response = test_client.get(f"/v1/artefacts/{artefact.id}/builds")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": artefact_build2.id,
            "revision": artefact_build2.revision,
            "architecture": artefact_build2.architecture,
            "test_executions": [],
        }
    ]


def test_get_artefact_builds_with_rerun_requested(
    test_client: TestClient, generator: DataGenerator
):
    a = generator.gen_artefact("beta")
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment()
    te = generator.gen_test_execution(ab, e)
    generator.gen_rerun_request(te)

    response = test_client.get(f"/v1/artefacts/{a.id}/builds")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": ab.id,
            "revision": ab.revision,
            "architecture": ab.architecture,
            "test_executions": [
                {
                    "id": te.id,
                    "ci_link": te.ci_link,
                    "c3_link": te.c3_link,
                    "status": te.status.value,
                    "environment": {
                        "id": e.id,
                        "name": e.name,
                        "architecture": e.architecture,
                    },
                    "review_decision": [],
                    "review_comment": "",
                    "is_rerun_requested": True,
                }
            ],
        }
    ]


def test_artefact_signoff_approve(test_client: TestClient, generator: DataGenerator):
    artefact = generator.gen_artefact("candidate")

    response = test_client.patch(
        f"/v1/artefacts/{artefact.id}",
        json={"status": ArtefactStatus.APPROVED},
    )

    assert response.status_code == 200
    assert artefact.status == ArtefactStatus.APPROVED
    assert response.json() == {
        "id": artefact.id,
        "name": artefact.name,
        "version": artefact.version,
        "track": artefact.track,
        "store": artefact.store,
        "series": artefact.series,
        "repo": artefact.repo,
        "stage": artefact.stage.name,
        "status": artefact.status,
        "assignee": None,
        "due_date": (
            artefact.due_date.strftime("%Y-%m-%d") if artefact.due_date else None
        ),
        "bug_link": "",
        "all_test_executions_count": 0,
        "completed_test_executions_count": 0,
    }


def test_artefact_signoff_disallow_approve(
    test_client: TestClient, test_execution: TestExecution
):
    artefact_id = test_execution.artefact_build.artefact_id
    response = test_client.patch(
        f"/v1/artefacts/{artefact_id}",
        json={"status": ArtefactStatus.APPROVED},
    )

    assert response.status_code == 400


def test_artefact_signoff_disallow_reject(
    test_client: TestClient, test_execution: TestExecution
):
    artefact_id = test_execution.artefact_build.artefact_id
    response = test_client.patch(
        f"/v1/artefacts/{artefact_id}",
        json={"status": ArtefactStatus.MARKED_AS_FAILED},
    )

    assert response.status_code == 400


def test_artefact_signoff_ignore_old_build_on_approve(
    test_client: TestClient, generator: DataGenerator
):
    artefact = generator.gen_artefact("candidate")
    build1 = generator.gen_artefact_build(artefact, revision=1)
    build2 = generator.gen_artefact_build(artefact, revision=1, architecture="arm64")
    build3 = generator.gen_artefact_build(artefact, revision=2)
    environment = generator.gen_environment()
    generator.gen_test_execution(build1, environment)
    generator.gen_test_execution(
        build2,
        environment,
        review_decision=[TestExecutionReviewDecision.APPROVED_ALL_TESTS_PASS],
    )
    generator.gen_test_execution(
        build3,
        environment,
        review_decision=[TestExecutionReviewDecision.APPROVED_ALL_TESTS_PASS],
    )

    response = test_client.patch(
        f"/v1/artefacts/{artefact.id}",
        json={"status": ArtefactStatus.APPROVED},
    )

    assert response.status_code == 200
    assert artefact.status == ArtefactStatus.APPROVED


def test_artefact_signoff_ignore_old_build_on_reject(
    test_client: TestClient, generator: DataGenerator
):
    artefact = generator.gen_artefact("candidate")
    build_1 = generator.gen_artefact_build(artefact, revision=1)
    build_2 = generator.gen_artefact_build(artefact, revision=2)
    environment = generator.gen_environment()
    generator.gen_test_execution(
        build_1, environment, review_decision=[TestExecutionReviewDecision.REJECTED]
    )
    generator.gen_test_execution(build_2, environment)

    response = test_client.patch(
        f"/v1/artefacts/{artefact.id}",
        json={"status": ArtefactStatus.MARKED_AS_FAILED},
    )

    assert response.status_code == 400
