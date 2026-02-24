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


from datetime import date, timedelta
from operator import itemgetter
from typing import Any

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from test_observer.data_access.models import Artefact, TestExecution
from test_observer.data_access.models_enums import (
    ArtefactBuildEnvironmentReviewDecision,
    ArtefactStatus,
    FamilyName,
    StageName,
)
from test_observer.common.permissions import Permission
from tests.data_generator import DataGenerator
from tests.conftest import make_authenticated_request


def test_get_artefacts_ignores_archived(
    generator: DataGenerator, test_client: TestClient
):
    a1 = generator.gen_artefact(
        stage=StageName.proposed,
        family=FamilyName.deb,
        name="linux-raspi",
        version="2",
        series="noble",
    )
    a2 = generator.gen_artefact(
        stage=StageName.beta,
        family=FamilyName.snap,
        name="pi-kernel",
        version="2",
        store="ubuntu",
        track="latest",
    )
    a3 = generator.gen_artefact(
        stage=StageName.beta,
        family=FamilyName.charm,
        name="postgresql",
        version="2",
        track="latest",
    )

    generator.gen_artefact(
        stage=StageName.proposed,
        family=FamilyName.deb,
        name="linux-raspi",
        version="1",
        series="noble",
        archived=True,
    )
    generator.gen_artefact(
        stage=StageName.beta,
        family=FamilyName.snap,
        name="pi-kernel",
        version="1",
        store="ubuntu",
        track="latest",
        archived=True,
    )
    generator.gen_artefact(
        stage=StageName.beta,
        family=FamilyName.charm,
        name="postgresql",
        version="1",
        track="latest",
        archived=True,
    )

    response = make_authenticated_request(
        lambda: test_client.get("/v1/artefacts"),
        Permission.view_artefact,
    )
    assert response.status_code == 200
    _assert_get_artefacts_response(response.json(), [a1, a2, a3])


@pytest.mark.parametrize(
    "artefact",
    [
        {
            "family": FamilyName.deb,
            "stage": StageName.proposed,
            "name": "server:linux-generic",
            "series": "noble",
        },
        {
            "family": FamilyName.snap,
            "stage": StageName.beta,
            "name": "core",
            "track": "latest",
            "store": "ubuntu",
        },
    ],
)
def test_get_artefacts_returns_latest_on_each_stage(
    generator: DataGenerator, test_client: TestClient, artefact: dict
):
    """If multiple versions of an artefact exist on the same stage, return the latest"""
    generator.gen_artefact(**artefact, version="1")
    new = generator.gen_artefact(**artefact, version="2")

    response = make_authenticated_request(
        lambda: test_client.get("/v1/artefacts", params={"family": artefact["family"]}),
        Permission.view_artefact,
    )
    assert response.status_code == 200
    _assert_get_artefacts_response(response.json(), [new])


def test_get_relevant_image_artefacts(
    test_client: TestClient, generator: DataGenerator
):
    old_image = generator.gen_image()
    new_image = generator.gen_image(
        sha256="someothersha256",
        version="20250101",
        created_at=old_image.created_at + timedelta(days=1),
    )

    response = make_authenticated_request(
        lambda: test_client.get("/v1/artefacts", params={"family": "image"}),
        Permission.view_artefact,
    )

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["sha256"] == new_image.sha256


def test_get_artefacts_treats_branches_as_unique(
    test_client: TestClient,
    generator: DataGenerator,
):
    generator.gen_artefact(StageName.beta)
    generator.gen_artefact(StageName.beta, branch="test-branch")

    response = make_authenticated_request(
        lambda: test_client.get("/v1/artefacts"),
        Permission.view_artefact,
    )

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2


def test_get_charm_artefacts_returns_all_non_archived(
    test_client: TestClient,
    generator: DataGenerator,
):
    """Charm family should return all non-archived artefacts, not just the latest"""
    a1 = generator.gen_artefact(
        stage=StageName.beta,
        family=FamilyName.charm,
        name="postgresql",
        version="1",
        track="latest",
        branch="main",
        archived=False,
    )
    a2 = generator.gen_artefact(
        stage=StageName.beta,
        family=FamilyName.charm,
        name="postgresql",
        version="2",
        track="latest",
        branch="main",
        archived=False,
    )
    # This one is archived, so shouldn't be returned
    generator.gen_artefact(
        stage=StageName.beta,
        family=FamilyName.charm,
        name="postgresql",
        version="0",
        track="latest",
        branch="main",
        archived=True,
    )

    response = make_authenticated_request(
        lambda: test_client.get("/v1/artefacts", params={"family": "charm"}),
        Permission.view_artefact,
    )

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    returned_ids = {r["id"] for r in response_data}
    assert returned_ids == {a1.id, a2.id}


def test_get_artefact(test_client: TestClient, generator: DataGenerator):
    """Should be able to fetch an existing artefact"""
    u = generator.gen_user()
    a = generator.gen_artefact(
        StageName.edge,
        status=ArtefactStatus.APPROVED,
        bug_link="localhost/bug",
        due_date=date(2024, 12, 24),
        reviewers=[u],
    )

    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefacts/{a.id}"),
        Permission.view_artefact,
    )

    assert response.status_code == 200
    _assert_get_artefact_response(response.json(), a)


def test_get_artefact_environment_reviews_counts_only_latest_build(
    test_client: TestClient, generator: DataGenerator
):
    a = generator.gen_artefact(StageName.beta)
    ab = generator.gen_artefact_build(artefact=a, revision=1)
    e = generator.gen_environment()
    # Test Execution for the first artefact build
    generator.gen_artefact_build_environment_review(ab, e)

    ab_second = generator.gen_artefact_build(artefact=a, revision=2)
    # Test Execution for the second artefact build
    generator.gen_artefact_build_environment_review(
        ab_second,
        e,
        review_decision=[
            ArtefactBuildEnvironmentReviewDecision.APPROVED_ALL_TESTS_PASS
        ],
    )

    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefacts/{a.id}"),
        Permission.view_artefact,
    )
    assert response.status_code == 200
    # Verify only the counts of the latest build is returned
    assert response.json()["all_environment_reviews_count"] == 1
    assert response.json()["completed_environment_reviews_count"] == 1


def test_get_artefact_environment_reviews_counts(
    test_client: TestClient,
    generator: DataGenerator,
    db_session: Session,
):
    a = generator.gen_artefact(StageName.beta)
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment()
    er = generator.gen_artefact_build_environment_review(ab, e)

    # Verify completed test execution count is zero, it is not reviewed yet
    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefacts/{a.id}"),
        Permission.view_artefact,
    )
    assert response.status_code == 200
    assert response.json()["all_environment_reviews_count"] == 1
    assert response.json()["completed_environment_reviews_count"] == 0

    er.review_decision = [
        ArtefactBuildEnvironmentReviewDecision.APPROVED_ALL_TESTS_PASS
    ]
    db_session.commit()
    db_session.refresh(er)

    # Verify completed test execution count is one, it is reviewed
    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefacts/{a.id}"),
        Permission.view_artefact,
    )
    assert response.status_code == 200
    assert response.json()["all_environment_reviews_count"] == 1
    assert response.json()["completed_environment_reviews_count"] == 1


def test_artefact_signoff_approve(test_client: TestClient, generator: DataGenerator):
    artefact = generator.gen_artefact(StageName.candidate)

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{artefact.id}",
            json={"status": ArtefactStatus.APPROVED},
        ),
        Permission.change_artefact,
    )

    assert response.status_code == 200
    assert artefact.status == ArtefactStatus.APPROVED


def test_artefact_signoff_disallow_approve(
    test_client: TestClient, generator: DataGenerator
):
    a = generator.gen_artefact(StageName.beta)
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment("env1")
    generator.gen_artefact_build_environment_review(ab, e)
    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{a.id}",
            json={"status": ArtefactStatus.APPROVED},
        ),
        Permission.change_artefact,
    )

    assert response.status_code == 400


def test_artefact_signoff_disallow_reject(
    test_client: TestClient, test_execution: TestExecution
):
    artefact_id = test_execution.artefact_build.artefact_id
    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{artefact_id}",
            json={"status": ArtefactStatus.MARKED_AS_FAILED},
        ),
        Permission.change_artefact,
    )

    assert response.status_code == 400


def test_artefact_signoff_ignore_old_build_on_approve(
    test_client: TestClient, generator: DataGenerator
):
    artefact = generator.gen_artefact(StageName.candidate)
    build1 = generator.gen_artefact_build(artefact, revision=1)
    build2 = generator.gen_artefact_build(artefact, revision=1, architecture="arm64")
    build3 = generator.gen_artefact_build(artefact, revision=2)
    environment = generator.gen_environment()
    generator.gen_artefact_build_environment_review(build1, environment)
    generator.gen_artefact_build_environment_review(
        build2,
        environment,
        review_decision=[
            ArtefactBuildEnvironmentReviewDecision.APPROVED_ALL_TESTS_PASS
        ],
    )
    generator.gen_artefact_build_environment_review(
        build3,
        environment,
        review_decision=[
            ArtefactBuildEnvironmentReviewDecision.APPROVED_ALL_TESTS_PASS
        ],
    )

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{artefact.id}",
            json={"status": ArtefactStatus.APPROVED},
        ),
        Permission.change_artefact,
    )

    assert response.status_code == 200
    assert artefact.status == ArtefactStatus.APPROVED


def test_artefact_signoff_ignore_old_build_on_reject(
    test_client: TestClient, generator: DataGenerator
):
    artefact = generator.gen_artefact(StageName.candidate)
    build_1 = generator.gen_artefact_build(artefact, revision=1)
    build_2 = generator.gen_artefact_build(artefact, revision=2)
    environment = generator.gen_environment()
    generator.gen_test_execution(build_1, environment)
    generator.gen_test_execution(build_2, environment)
    generator.gen_artefact_build_environment_review(
        build_1,
        environment,
        review_decision=[ArtefactBuildEnvironmentReviewDecision.REJECTED],
    )
    generator.gen_artefact_build_environment_review(build_2, environment)

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{artefact.id}",
            json={"status": ArtefactStatus.MARKED_AS_FAILED},
        ),
        Permission.change_artefact,
    )

    assert response.status_code == 400


def test_artefact_rejection_requires_comment(
    test_client: TestClient, test_execution: TestExecution
):
    # Reject an environment as that's required to reject an artefact
    test_execution.artefact_build.environment_reviews[0].review_decision = [
        ArtefactBuildEnvironmentReviewDecision.REJECTED
    ]

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{test_execution.artefact_build.artefact_id}",
            json={"status": ArtefactStatus.MARKED_AS_FAILED},
        ),
        Permission.change_artefact,
    )

    assert response.status_code == 400

    test_execution.artefact_build.artefact.comment = "some comment"

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{test_execution.artefact_build.artefact_id}",
            json={"status": ArtefactStatus.MARKED_AS_FAILED},
        ),
        Permission.change_artefact,
    )

    assert response.status_code == 200
    assert (
        test_execution.artefact_build.artefact.status == ArtefactStatus.MARKED_AS_FAILED
    )


def test_artefact_archive(test_client: TestClient, generator: DataGenerator):
    artefact = generator.gen_artefact(StageName.candidate, archived=False)

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{artefact.id}",
            json={"archived": True},
        ),
        Permission.change_artefact,
    )

    assert response.status_code == 200
    assert artefact.archived


def test_artefact_unarchive(test_client: TestClient, generator: DataGenerator):
    artefact = generator.gen_artefact(StageName.candidate, archived=True)

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{artefact.id}",
            json={"archived": False},
        ),
        Permission.change_artefact,
    )

    assert response.status_code == 200
    assert not artefact.archived


def test_artefact_promote(test_client: TestClient, generator: DataGenerator):
    artefact = generator.gen_artefact(StageName.candidate)

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{artefact.id}",
            json={"stage": StageName.stable},
        ),
        Permission.change_artefact,
    )

    assert response.status_code == 200
    assert artefact.stage == StageName.stable


def test_artefact_promote_invalid_stage(
    test_client: TestClient,
    generator: DataGenerator,
):
    artefact = generator.gen_artefact(family=FamilyName.charm)

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{artefact.id}",
            json={"stage": StageName.current},
        ),
        Permission.change_artefact,
    )

    assert response.status_code == 400


def test_artefact_promote_unknown_stage(
    test_client: TestClient,
    generator: DataGenerator,
):
    artefact = generator.gen_artefact()

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{artefact.id}",
            json={"stage": "unknown"},
        ),
        Permission.change_artefact,
    )

    assert response.status_code > 400


def test_update_artefact_comment(test_client: TestClient, generator: DataGenerator):
    a = generator.gen_artefact()
    comment = "Updated comment"

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{a.id}",
            json={"comment": comment},
        ),
        Permission.change_artefact,
    )

    assert response.status_code == 200
    assert a.comment == comment


def test_update_artefact_assignee(test_client: TestClient, generator: DataGenerator):
    a = generator.gen_artefact()
    u = generator.gen_user()

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{a.id}",
            json={"reviewer_ids": [u.id]},
        ),
        Permission.change_artefact,
    )

    assert response.status_code == 200
    assert a.reviewers == [u]


def test_update_artefact_assignee_nonexistent_user(
    test_client: TestClient, generator: DataGenerator
):
    a = generator.gen_artefact()
    nonexistent_user_id = 99999

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{a.id}",
            json={"reviewer_ids": [nonexistent_user_id]},
        ),
        Permission.change_artefact,
    )

    assert response.status_code == 422
    assert "User with id 99999 not found" in response.json()["detail"]


def test_update_artefact_assignee_clear(
    test_client: TestClient, generator: DataGenerator
):
    u = generator.gen_user()
    a = generator.gen_artefact(reviewers=[u])

    # Verify assignee is set initially
    assert a.reviewers == [u]

    # Clear the assignee
    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{a.id}",
            json={"reviewer_ids": None},
        ),
        Permission.change_artefact,
    )

    assert response.status_code == 200
    assert a.reviewers == []


def test_update_artefact_assignee_by_email(
    test_client: TestClient, generator: DataGenerator
):
    a = generator.gen_artefact()
    u = generator.gen_user()

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{a.id}",
            json={"reviewer_emails": [u.email]},
        ),
        Permission.change_artefact,
    )

    assert response.status_code == 200
    assert a.reviewers == [u]


def test_update_artefact_assignee_by_email_nonexistent(
    test_client: TestClient, generator: DataGenerator
):
    a = generator.gen_artefact()
    nonexistent_email = "nonexistent@example.com"

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{a.id}",
            json={"reviewer_emails": [nonexistent_email]},
        ),
        Permission.change_artefact,
    )

    assert response.status_code == 422
    expected_msg = f"User with email '{nonexistent_email}' not found"
    assert expected_msg in response.json()["detail"]


def test_update_artefact_assignee_clear_by_email(
    test_client: TestClient, generator: DataGenerator
):
    u = generator.gen_user()
    a = generator.gen_artefact(reviewers=[u])

    # Verify assignee is set initially
    assert a.reviewers == [u]

    # Clear the assignee using email
    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{a.id}",
            json={"reviewer_emails": None},
        ),
        Permission.change_artefact,
    )

    assert response.status_code == 200
    assert a.reviewers == []


def test_update_artefact_assignee_both_id_and_email_error(
    test_client: TestClient, generator: DataGenerator
):
    a = generator.gen_artefact()
    u = generator.gen_user()

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{a.id}",
            json={
                "reviewer_ids": [u.id],
                "reviewer_emails": [u.email],
            },
        ),
        Permission.change_artefact,
    )

    assert response.status_code == 422
    expected_msg = "Cannot specify both reviewer_ids and reviewer_emails"
    assert expected_msg in response.json()["detail"]


def test_get_artefact_versions(test_client: TestClient, generator: DataGenerator):
    artefact1 = generator.gen_artefact(StageName.beta, version="1")
    artefact2 = generator.gen_artefact(StageName.beta, version="2")
    artefact3 = generator.gen_artefact(StageName.beta, version="3", branch="test")

    expected_result = [
        {"version": "2", "artefact_id": artefact2.id},
        {"version": "1", "artefact_id": artefact1.id},
    ]

    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefacts/{artefact1.id}/versions"),
        Permission.view_artefact,
    )
    assert response.status_code == 200
    assert response.json() == expected_result

    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefacts/{artefact2.id}/versions"),
        Permission.view_artefact,
    )
    assert response.status_code == 200
    assert response.json() == expected_result

    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefacts/{artefact3.id}/versions"),
        Permission.view_artefact,
    )
    assert response.status_code == 200
    assert response.json() == [{"version": "3", "artefact_id": artefact3.id}]


def _assert_get_artefacts_response(
    response_json: list[dict[str, Any]], artefacts: list[Artefact]
) -> None:
    for r, a in zip(
        sorted(response_json, key=itemgetter("id")), artefacts, strict=True
    ):
        _assert_get_artefact_response(r, a)


def _assert_get_artefact_response(response: dict[str, Any], artefact: Artefact) -> None:
    expected = {
        "id": artefact.id,
        "name": artefact.name,
        "version": artefact.version,
        "track": artefact.track,
        "store": artefact.store,
        "branch": artefact.branch,
        "series": artefact.series,
        "repo": artefact.repo,
        "source": artefact.source,
        "stage": artefact.stage,
        "os": artefact.os,
        "release": artefact.release,
        "owner": artefact.owner,
        "sha256": artefact.sha256,
        "image_url": artefact.image_url,
        "status": artefact.status,
        "comment": artefact.comment,
        "archived": artefact.archived,
        "family": artefact.family,
        "reviewers": [],
        "due_date": (
            artefact.due_date.strftime("%Y-%m-%d") if artefact.due_date else None
        ),
        "bug_link": artefact.bug_link,
        "all_environment_reviews_count": artefact.all_environment_reviews_count,
        "completed_environment_reviews_count": artefact.completed_environment_reviews_count,  # noqa: E501
        "created_at": artefact.created_at.isoformat(),
    }
    if artefact.reviewers:
        expected["reviewers"] = [{
            "id": r.id,
            "email": r.email,
            "launchpad_email": r.email,
            "launchpad_handle": r.launchpad_handle,
            "name": r.name,
        } for r in artefact.reviewers]
    assert response == expected
