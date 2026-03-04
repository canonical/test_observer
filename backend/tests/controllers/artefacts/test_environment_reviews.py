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

from operator import itemgetter

from fastapi.testclient import TestClient

from test_observer.common.permissions import Permission
from test_observer.data_access.models_enums import (
    ArtefactBuildEnvironmentReviewDecision,
    StageName,
)
from tests.conftest import make_authenticated_request
from tests.data_generator import DataGenerator


def test_get_404_when_artefact_is_not_found(test_client: TestClient):
    response = make_authenticated_request(
        lambda: test_client.get("/v1/artefacts/1/environment-reviews"),
        Permission.view_environment_review,
    )
    assert response.status_code == 404


def test_get_no_environment_reviews_exist(test_client: TestClient, generator: DataGenerator):
    a = generator.gen_artefact(StageName.beta)
    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefacts/{a.id}/environment-reviews"),
        Permission.view_environment_review,
    )
    assert response.status_code == 200


def test_get_with_two_environment_reviews(test_client: TestClient, generator: DataGenerator):
    a = generator.gen_artefact(StageName.beta)
    ab = generator.gen_artefact_build(a)
    e1 = generator.gen_environment("env1")
    e2 = generator.gen_environment("env2")
    review1 = generator.gen_artefact_build_environment_review(ab, e1)
    review2 = generator.gen_artefact_build_environment_review(ab, e2)

    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefacts/{a.id}/environment-reviews"),
        Permission.view_environment_review,
    )
    assert response.status_code == 200
    assert sorted(response.json(), key=itemgetter("id")) == [
        {
            "id": review1.id,
            "review_decision": review1.review_decision,
            "review_comment": review1.review_comment,
            "environment": {
                "id": e1.id,
                "name": e1.name,
                "architecture": e1.architecture,
            },
            "artefact_build": {
                "id": ab.id,
                "architecture": ab.architecture,
                "revision": ab.revision,
            },
        },
        {
            "id": review2.id,
            "review_decision": review2.review_decision,
            "review_comment": review2.review_comment,
            "environment": {
                "id": e2.id,
                "name": e2.name,
                "architecture": e2.architecture,
            },
            "artefact_build": {
                "id": ab.id,
                "architecture": ab.architecture,
                "revision": ab.revision,
            },
        },
    ]


def test_get_only_considers_latest_builds(test_client: TestClient, generator: DataGenerator):
    a = generator.gen_artefact(StageName.beta)
    ab1 = generator.gen_artefact_build(a, revision=1)
    ab2 = generator.gen_artefact_build(a, revision=2)
    e1 = generator.gen_environment("env1")
    e2 = generator.gen_environment("env2")
    generator.gen_artefact_build_environment_review(ab1, e1)
    review2 = generator.gen_artefact_build_environment_review(ab2, e2)

    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefacts/{a.id}/environment-reviews"),
        Permission.view_environment_review,
    )
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": review2.id,
            "review_decision": review2.review_decision,
            "review_comment": review2.review_comment,
            "environment": {
                "id": review2.environment.id,
                "name": review2.environment.name,
                "architecture": review2.environment.architecture,
            },
            "artefact_build": {
                "id": review2.artefact_build.id,
                "architecture": review2.artefact_build.architecture,
                "revision": review2.artefact_build.revision,
            },
        },
    ]


def test_review_an_environment(test_client: TestClient, generator: DataGenerator):
    a = generator.gen_artefact(StageName.beta)
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment("env1")
    er = generator.gen_artefact_build_environment_review(ab, e)

    update = {
        "review_comment": "Some Comment",
        "review_decision": [ArtefactBuildEnvironmentReviewDecision.APPROVED_INCONSISTENT_TEST],
    }
    response = make_authenticated_request(
        lambda: test_client.patch(f"/v1/artefacts/{a.id}/environment-reviews/{er.id}", json=update),
        Permission.change_environment_review,
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": er.id,
        "review_decision": update["review_decision"],
        "review_comment": update["review_comment"],
        "environment": {
            "id": e.id,
            "name": e.name,
            "architecture": e.architecture,
        },
        "artefact_build": {
            "id": ab.id,
            "revision": ab.revision,
            "architecture": ab.architecture,
        },
    }


def test_bulk_review_multiple_environments(
    test_client: TestClient, generator: DataGenerator
):
    """Test bulk reviewing multiple environments at once."""
    a = generator.gen_artefact(StageName.beta)
    ab = generator.gen_artefact_build(a)
    e1 = generator.gen_environment("env1")
    e2 = generator.gen_environment("env2")
    er1 = generator.gen_artefact_build_environment_review(ab, e1)
    er2 = generator.gen_artefact_build_environment_review(ab, e2)

    update = [
        {
            "id": er1.id,
            "review_comment": "Approved env1",
            "review_decision": [
                ArtefactBuildEnvironmentReviewDecision.APPROVED_INCONSISTENT_TEST
            ],
        },
        {
            "id": er2.id,
            "review_comment": "Approved env2",
            "review_decision": [
                ArtefactBuildEnvironmentReviewDecision.APPROVED_INCONSISTENT_TEST
            ],
        },
    ]

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{a.id}/environment-reviews",
            json=update,
        ),
        Permission.change_environment_review,
    )

    assert response.status_code == 200
    reviews = response.json()
    assert len(reviews) == 2
    assert sorted([r["id"] for r in reviews]) == sorted([er1.id, er2.id])

    for review in reviews:
        if review["id"] == er1.id:
            assert review["review_comment"] == "Approved env1"
            assert review["review_decision"] == [
                ArtefactBuildEnvironmentReviewDecision.APPROVED_INCONSISTENT_TEST
            ]
        elif review["id"] == er2.id:
            assert review["review_comment"] == "Approved env2"
            assert review["review_decision"] == [
                ArtefactBuildEnvironmentReviewDecision.APPROVED_INCONSISTENT_TEST
            ]


def test_bulk_review_with_same_comment_and_decision(
    test_client: TestClient, generator: DataGenerator
):
    """Test bulk reviewing with same comment and decision for multiple environments."""
    a = generator.gen_artefact(StageName.beta)
    ab = generator.gen_artefact_build(a)
    e1 = generator.gen_environment("env1")
    e2 = generator.gen_environment("env2")
    e3 = generator.gen_environment("env3")
    er1 = generator.gen_artefact_build_environment_review(ab, e1)
    er2 = generator.gen_artefact_build_environment_review(ab, e2)
    er3 = generator.gen_artefact_build_environment_review(ab, e3)

    # Apply the same review to all environments
    update = [
        {"id": er1.id, "review_comment": "All good"},
        {"id": er2.id, "review_comment": "All good"},
        {"id": er3.id, "review_comment": "All good"},
    ]

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{a.id}/environment-reviews",
            json=update,
        ),
        Permission.change_environment_review,
    )

    assert response.status_code == 200
    reviews = response.json()
    assert len(reviews) == 3
    for review in reviews:
        assert review["review_comment"] == "All good"


def test_bulk_review_rejects_if_review_belongs_to_different_artefact(
    test_client: TestClient, generator: DataGenerator
):
    """Test that bulk review silently skips reviews from a different artefact."""
    a1 = generator.gen_artefact(StageName.beta, name="artefact1")
    a2 = generator.gen_artefact(StageName.beta, name="artefact2")
    ab1 = generator.gen_artefact_build(a1)
    ab2 = generator.gen_artefact_build(a2)
    e1 = generator.gen_environment("env1")
    e2 = generator.gen_environment("env2")
    er1 = generator.gen_artefact_build_environment_review(ab1, e1)
    er2 = generator.gen_artefact_build_environment_review(ab2, e2)

    update = [
        {"id": er1.id, "review_comment": "Comment"},
        {"id": er2.id, "review_comment": "Comment"},
    ]

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{a1.id}/environment-reviews",
            json=update,
        ),
        Permission.change_environment_review,
    )

    assert response.status_code == 200
    reviews = response.json()
    # Only er1 should be updated; er2 is silently skipped as it belongs to a2
    assert len(reviews) == 1
    assert reviews[0]["id"] == er1.id
    assert reviews[0]["review_comment"] == "Comment"


def test_bulk_review_reset_review(test_client: TestClient, generator: DataGenerator):
    """Test resetting reviews (clearing comment and decisions) in bulk."""
    a = generator.gen_artefact(StageName.beta)
    ab = generator.gen_artefact_build(a)
    e1 = generator.gen_environment("env1")
    e2 = generator.gen_environment("env2")
    er1 = generator.gen_artefact_build_environment_review(
        ab,
        e1,
        review_decision=[ArtefactBuildEnvironmentReviewDecision.REJECTED],
        review_comment="rejected",
    )
    er2 = generator.gen_artefact_build_environment_review(
        ab,
        e2,
        review_decision=[ArtefactBuildEnvironmentReviewDecision.REJECTED],
        review_comment="rejected",
    )

    update = [
        {"id": er1.id, "review_decision": [], "review_comment": ""},
        {"id": er2.id, "review_decision": [], "review_comment": ""},
    ]

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{a.id}/environment-reviews",
            json=update,
        ),
        Permission.change_environment_review,
    )

    assert response.status_code == 200
    reviews = response.json()
    assert len(reviews) == 2
    for review in reviews:
        assert review["review_decision"] == []
        assert review["review_comment"] == ""


def test_requires_review_to_belong_to_artefact(test_client: TestClient, generator: DataGenerator):
    a1 = generator.gen_artefact(StageName.beta, name="a1")
    a2 = generator.gen_artefact(StageName.beta, name="a2")
    ab = generator.gen_artefact_build(a1)
    e = generator.gen_environment("env1")
    er = generator.gen_artefact_build_environment_review(ab, e)

    response = make_authenticated_request(
        lambda: test_client.patch(f"/v1/artefacts/{a2.id}/environment-reviews/{er.id}", json={}),
        Permission.change_environment_review,
    )

    assert response.status_code == 422


def test_environment_review_fails_if_both_rejected_and_approved(test_client: TestClient, generator: DataGenerator):
    a = generator.gen_artefact(StageName.beta)
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment("env1")
    er = generator.gen_artefact_build_environment_review(ab, e)

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{a.id}/environment-reviews/{er.id}",
            json={
                "review_decision": [
                    ArtefactBuildEnvironmentReviewDecision.REJECTED.name,
                    ArtefactBuildEnvironmentReviewDecision.APPROVED_INCONSISTENT_TEST.name,
                ],
            },
        ),
        Permission.change_environment_review,
    )

    assert response.status_code == 422


def test_environment_review_reset_review(test_client: TestClient, generator: DataGenerator):
    a = generator.gen_artefact(StageName.beta)
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment("env1")
    er = generator.gen_artefact_build_environment_review(
        ab,
        e,
        review_decision=[ArtefactBuildEnvironmentReviewDecision.REJECTED],
        review_comment="some comment",
    )

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/artefacts/{a.id}/environment-reviews/{er.id}",
            json={"review_decision": [], "review_comment": ""},
        ),
        Permission.change_environment_review,
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": er.id,
        "review_decision": [],
        "review_comment": "",
        "environment": {
            "id": e.id,
            "name": e.name,
            "architecture": e.architecture,
        },
        "artefact_build": {
            "id": ab.id,
            "revision": ab.revision,
            "architecture": ab.architecture,
        },
    }
