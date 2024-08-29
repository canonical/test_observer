from collections.abc import Callable
from typing import Any, TypeAlias

import pytest
from fastapi.testclient import TestClient
from httpx import Response

endpoint = "/v1/test-cases/reported-issues"
valid_post_data = {
    "template_id": "template 1",
    "url": "http://issue.link/",
    "description": "some description",
}


@pytest.fixture
def post(test_client: TestClient):
    def post_helper(data: Any) -> Response:  # noqa: ANN401
        return test_client.post(endpoint, json=data)

    return post_helper


@pytest.fixture
def get(test_client: TestClient):
    def get_helper(query_parameters: dict[str, str] | None = None) -> Response:
        return test_client.get(endpoint, params=query_parameters)

    return get_helper


Post: TypeAlias = Callable[[Any], Response]
Get: TypeAlias = Callable[..., Response]


def test_empty_get(get: Get):
    response = get()
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("field", ["template_id", "url", "description"])
def test_post_requires_field(post: Post, field: str):
    data = {k: v for k, v in valid_post_data.items() if k != field}
    response = post(data)
    _assert_fails_validation(response, field, "missing")


def test_post_validates_url(post: Post):
    response = post({**valid_post_data, "url": "invalid url"})
    _assert_fails_validation(response, "url", "url_parsing")


def test_valid_post(post: Post):
    response = post(valid_post_data)
    assert response.status_code == 200
    _assert_reported_issue(response.json(), valid_post_data)


def test_post_three_then_get(post: Post, get: Get):
    issue1 = {**valid_post_data, "description": "Description 1"}
    issue2 = {**valid_post_data, "description": "Description 2"}
    issue3 = {**valid_post_data, "description": "Description 3"}

    post(issue1)
    post(issue2)
    post(issue3)

    response = get()
    assert response.status_code == 200
    json = response.json()
    _assert_reported_issue(json[0], issue1)
    _assert_reported_issue(json[1], issue2)
    _assert_reported_issue(json[2], issue3)


def test_get_specific_template_id(post: Post, get: Get):
    issue1 = {**valid_post_data, "template_id": "Template 1"}
    issue2 = {**valid_post_data, "template_id": "Template 2"}

    post(issue1)
    post(issue2)

    response = get({"template_id": "Template 2"})
    assert response.status_code == 200
    json = response.json()
    assert len(json) == 1
    _assert_reported_issue(json[0], issue2)


def _assert_fails_validation(response: Response, field: str, type: str) -> None:
    assert response.status_code == 422
    problem = response.json()["detail"][0]
    assert problem["type"] == type
    assert problem["loc"] == ["body", field]


def _assert_reported_issue(value: dict, expected: dict) -> None:
    assert value["template_id"] == expected["template_id"]
    assert value["url"] == expected["url"]
    assert value["description"] == expected["description"]
    assert isinstance(value["id"], int)
    assert isinstance(value["created_at"], str)
    assert isinstance(value["updated_at"], str)
