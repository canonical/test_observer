from collections.abc import Callable
from operator import itemgetter
from typing import Any, TypeAlias

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from test_observer.data_access.models import TestExecution
from tests.data_generator import DataGenerator

reruns_url = "/v1/test-executions/reruns"


@pytest.fixture
def post(test_client: TestClient):
    def post_helper(data: Any) -> Response:  # noqa: ANN401
        return test_client.post(reruns_url, json=data)

    return post_helper


@pytest.fixture
def get(test_client: TestClient):
    def get_helper() -> Response:
        return test_client.get(reruns_url)

    return get_helper


@pytest.fixture
def delete(test_client: TestClient):
    def delete_helper(data: Any) -> Response:  # noqa: ANN401
        return test_client.request("DELETE", reruns_url, json=data)

    return delete_helper


Post: TypeAlias = Callable[[Any], Response]
Get: TypeAlias = Callable[[], Response]
Delete: TypeAlias = Callable[[Any], Response]


def test_post_no_data_returns_422(post: Post):
    assert post(None).status_code == 422


def test_post_invalid_id_returns_404_with_message(post: Post):
    response = post({"test_execution_ids": [1]})
    assert response.status_code == 404
    assert response.json()["detail"] == "Didn't find test executions with provided ids"


def test_valid_post(post: Post, test_execution: TestExecution):
    test_execution.ci_link = "ci.link"
    response = post({"test_execution_ids": [test_execution.id]})

    assert response.status_code == 200
    assert response.json() == [
        {
            "test_execution_id": test_execution.id,
            "ci_link": test_execution.ci_link,
            "family": test_execution.artefact_build.artefact.family.name,
        }
    ]


def test_post_with_valid_and_invalid_ids(post: Post, test_execution: TestExecution):
    test_execution.ci_link = "ci.link"
    response = post({"test_execution_ids": [test_execution.id, test_execution.id + 1]})
    assert response.status_code == 207


def test_get_returns_200_with_empty_list(get: Get):
    response = get()
    assert response.status_code == 200
    assert response.json() == []


def test_get_after_one_post(get: Get, post: Post, test_execution: TestExecution):
    test_execution.ci_link = "ci.link"

    post({"test_execution_ids": [test_execution.id]})

    assert get().json() == [
        {
            "test_execution_id": test_execution.id,
            "ci_link": test_execution.ci_link,
            "family": test_execution.artefact_build.artefact.family.name,
        }
    ]


def test_get_after_two_identical_posts(
    get: Get, post: Post, test_execution: TestExecution
):
    test_execution.ci_link = "ci.link"

    post({"test_execution_ids": [test_execution.id]})
    post({"test_execution_ids": [test_execution.id]})

    assert get().json() == [
        {
            "test_execution_id": test_execution.id,
            "ci_link": test_execution.ci_link,
            "family": test_execution.artefact_build.artefact.family.name,
        }
    ]


def test_get_after_two_different_posts(
    get: Get, post: Post, test_execution: TestExecution, generator: DataGenerator
):
    te1 = test_execution
    te1.ci_link = "ci1.link"

    e2 = generator.gen_environment("desktop")
    te2 = generator.gen_test_execution(te1.artefact_build, e2, ci_link="ci2.link")

    post({"test_execution_ids": [te1.id]})
    post({"test_execution_ids": [te2.id]})

    assert get().json() == [
        {
            "test_execution_id": te1.id,
            "ci_link": te1.ci_link,
            "family": te1.artefact_build.artefact.family.name,
        },
        {
            "test_execution_id": te2.id,
            "ci_link": te2.ci_link,
            "family": te2.artefact_build.artefact.family.name,
        },
    ]


def test_get_after_post_with_two_test_execution_ids(
    get: Get, post: Post, generator: DataGenerator
):
    a = generator.gen_artefact("beta")
    ab = generator.gen_artefact_build(a)
    e1 = generator.gen_environment("e1")
    e2 = generator.gen_environment("e2")
    te1 = generator.gen_test_execution(ab, e1, ci_link="ci1.link")
    te2 = generator.gen_test_execution(ab, e2, ci_link="ci2.link")

    post({"test_execution_ids": [te1.id, te2.id]})

    assert sorted(get().json(), key=itemgetter("test_execution_id")) == [
        {
            "test_execution_id": te1.id,
            "ci_link": te1.ci_link,
            "family": te1.artefact_build.artefact.family.name,
        },
        {
            "test_execution_id": te2.id,
            "ci_link": te2.ci_link,
            "family": te2.artefact_build.artefact.family.name,
        },
    ]


def test_post_delete_get(
    get: Get, post: Post, delete: Delete, test_execution: TestExecution
):
    test_execution.ci_link = "ci.link"
    post({"test_execution_ids": [test_execution.id]})
    response = delete({"test_execution_ids": [test_execution.id]})

    assert response.status_code == 200
    assert get().json() == []
