from collections.abc import Callable
from typing import Any, TypeAlias

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from tests.asserts import assert_fails_validation

endpoint = "/v1/test-cases/reported-issues"
valid_post_data = {
    "template_id": "template 1",
    "case_name": "case",
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


@pytest.fixture
def put(test_client: TestClient):
    def put_helper(id: int, data: Any) -> Response:  # noqa: ANN401
        return test_client.put(f"{endpoint}/{id}", json=data)

    return put_helper


@pytest.fixture
def delete(test_client: TestClient):
    def delete_helper(id: int) -> Response:
        return test_client.delete(f"{endpoint}/{id}")

    return delete_helper


Post: TypeAlias = Callable[[Any], Response]
Put: TypeAlias = Callable[[int, Any], Response]
Get: TypeAlias = Callable[..., Response]
Delete: TypeAlias = Callable[[int], Response]


def test_empty_get(get: Get):
    response = get()
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("field", ["url", "description"])
def test_post_requires_field(post: Post, field: str):
    data = {k: v for k, v in valid_post_data.items() if k != field}
    response = post(data)
    assert_fails_validation(response, field, "missing")


def test_post_requires_template_id_or_case_name(post: Post):
    data = {**valid_post_data}
    data.pop("template_id")
    data.pop("case_name")
    response = post(data)

    assert response.status_code == 422


def test_post_validates_url(post: Post):
    response = post({**valid_post_data, "url": "invalid url"})
    assert_fails_validation(response, "url", "url_parsing")


def test_valid_template_id_post(post: Post):
    data = {k: v for k, v in valid_post_data.items() if k != "case_name"}
    response = post(data)
    assert response.status_code == 200
    _assert_reported_issue(response.json(), data)


def test_valid_case_name_post(post: Post):
    data = {k: v for k, v in valid_post_data.items() if k != "template_id"}
    response = post(data)
    assert response.status_code == 200
    _assert_reported_issue(response.json(), data)


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


def test_get_specific_case_name(post: Post, get: Get):
    issue1 = {**valid_post_data, "case_name": "Case 1"}
    issue2 = {**valid_post_data, "case_name": "Case 2"}

    post(issue1)
    post(issue2)

    response = get({"case_name": "Case 2"})
    assert response.status_code == 200
    json = response.json()
    assert len(json) == 1
    _assert_reported_issue(json[0], issue2)


def test_update_description(post: Post, get: Get, put: Put):
    response = post(valid_post_data)
    issue = response.json()
    issue["description"] = "Updated"
    response = put(issue["id"], issue)

    assert response.status_code == 200
    _assert_reported_issue(response.json(), issue)

    response = get()
    _assert_reported_issue(response.json()[0], issue)


def test_delete_issue(post: Post, get: Get, delete: Delete):
    response = post(valid_post_data)

    response = delete(response.json()["id"])
    assert response.status_code == 200

    response = get()
    assert response.json() == []


def _assert_reported_issue(value: dict, expected: dict) -> None:
    if "template_id" in expected:
        assert value["template_id"] == expected["template_id"]

    if "case_name" in expected:
        assert value["case_name"] == expected["case_name"]

    assert value["url"] == expected["url"]
    assert value["description"] == expected["description"]
    assert isinstance(value["id"], int)
    assert isinstance(value["created_at"], str)
    assert isinstance(value["updated_at"], str)
