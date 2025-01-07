from operator import itemgetter

from fastapi.testclient import TestClient

from test_observer.data_access.models_enums import (
    ArtefactBuildEnvironmentReviewDecision,
    StageName,
)
from tests.data_generator import DataGenerator


def test_get_404_when_artefact_is_not_found(test_client: TestClient):
    response = test_client.get("/v1/artefacts/1/environment-reviews")
    assert response.status_code == 404


def test_get_no_environment_reviews_exist(
    test_client: TestClient, generator: DataGenerator
):
    a = generator.gen_artefact(StageName.beta)
    response = test_client.get(f"/v1/artefacts/{a.id}/environment-reviews")
    assert response.status_code == 200


def test_get_with_two_environment_reviews(
    test_client: TestClient, generator: DataGenerator
):
    a = generator.gen_artefact(StageName.beta)
    ab = generator.gen_artefact_build(a)
    e1 = generator.gen_environment("env1")
    e2 = generator.gen_environment("env2")
    review1 = generator.gen_artefact_build_environment_review(ab, e1)
    review2 = generator.gen_artefact_build_environment_review(ab, e2)

    response = test_client.get(f"/v1/artefacts/{a.id}/environment-reviews")
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


def test_get_only_consideres_latest_builds(
    test_client: TestClient, generator: DataGenerator
):
    a = generator.gen_artefact(StageName.beta)
    ab1 = generator.gen_artefact_build(a, revision=1)
    ab2 = generator.gen_artefact_build(a, revision=2)
    e1 = generator.gen_environment("env1")
    e2 = generator.gen_environment("env2")
    generator.gen_artefact_build_environment_review(ab1, e1)
    review2 = generator.gen_artefact_build_environment_review(ab2, e2)

    response = test_client.get(f"/v1/artefacts/{a.id}/environment-reviews")
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
        "review_decision": [
            ArtefactBuildEnvironmentReviewDecision.APPROVED_INCONSISTENT_TEST
        ],
    }
    response = test_client.patch(
        f"/v1/artefacts/{a.id}/environment-reviews/{er.id}", json=update
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


def test_requires_review_to_belong_to_artefact(
    test_client: TestClient, generator: DataGenerator
):
    a1 = generator.gen_artefact(StageName.beta, name="a1")
    a2 = generator.gen_artefact(StageName.beta, name="a2")
    ab = generator.gen_artefact_build(a1)
    e = generator.gen_environment("env1")
    er = generator.gen_artefact_build_environment_review(ab, e)

    response = test_client.patch(
        f"/v1/artefacts/{a2.id}/environment-reviews/{er.id}", json={}
    )

    assert response.status_code == 422


def test_environment_review_fails_if_both_rejected_and_approved(
    test_client: TestClient, generator: DataGenerator
):
    a = generator.gen_artefact(StageName.beta)
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment("env1")
    er = generator.gen_artefact_build_environment_review(ab, e)

    response = test_client.patch(
        f"/v1/artefacts/{a.id}/environment-reviews/{er.id}",
        json={
            "review_decision": [
                ArtefactBuildEnvironmentReviewDecision.REJECTED.name,
                ArtefactBuildEnvironmentReviewDecision.APPROVED_INCONSISTENT_TEST.name,
            ],
        },
    )

    assert response.status_code == 422


def test_environment_review_reset_review(
    test_client: TestClient, generator: DataGenerator
):
    a = generator.gen_artefact(StageName.beta)
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment("env1")
    er = generator.gen_artefact_build_environment_review(
        ab,
        e,
        review_decision=[ArtefactBuildEnvironmentReviewDecision.REJECTED],
        review_comment="some comment",
    )

    response = test_client.patch(
        f"/v1/artefacts/{a.id}/environment-reviews/{er.id}",
        json={"review_decision": [], "review_comment": ""},
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
