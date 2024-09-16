import pytest
from fastapi.testclient import TestClient

from tests.asserts import assert_fails_validation

endpoint = "/v1/environments/reported-issues"
valid_post_data = {
    "environment_name": "template 1",
    "url": "http://issue.link/",
    "description": "some description",
}


def test_empty_get(test_client: TestClient):
    response = test_client.get(endpoint)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("field", ["url", "description", "environment_name"])
def test_post_requires_field(test_client: TestClient, field: str):
    data = {k: v for k, v in valid_post_data.items() if k != field}
    response = test_client.post(endpoint, json=data)
    assert_fails_validation(response, field, "missing")


def test_post_validates_url(test_client: TestClient):
    data = {**valid_post_data, "url": "invalid url"}
    response = test_client.post(endpoint, json=data)
    assert_fails_validation(response, "url", "url_parsing")


def test_valid_post(test_client: TestClient):
    response = test_client.post(endpoint, json=valid_post_data)
    assert response.status_code == 200
    _assert_reported_issue(response.json(), valid_post_data)


def test_post_three_then_get(test_client: TestClient):
    issue1 = {**valid_post_data, "description": "Description 1"}
    issue2 = {**valid_post_data, "description": "Description 2"}
    issue3 = {**valid_post_data, "description": "Description 3"}

    test_client.post(endpoint, json=issue1)
    test_client.post(endpoint, json=issue2)
    test_client.post(endpoint, json=issue3)

    response = test_client.get(endpoint)
    assert response.status_code == 200
    json = response.json()
    _assert_reported_issue(json[0], issue1)
    _assert_reported_issue(json[1], issue2)
    _assert_reported_issue(json[2], issue3)


def test_update_description(test_client: TestClient):
    response = test_client.post(endpoint, json=valid_post_data)
    issue = response.json()
    issue["description"] = "Updated"
    response = test_client.put(f"{endpoint}/{issue['id']}", json=issue)

    assert response.status_code == 200
    _assert_reported_issue(response.json(), issue)

    response = test_client.get(endpoint)
    _assert_reported_issue(response.json()[0], issue)


def test_delete_issue(test_client: TestClient):
    response = test_client.post(endpoint, json=valid_post_data)
    issue_id = response.json()["id"]

    response = test_client.delete(f"{endpoint}/{issue_id}")
    assert response.status_code == 200

    response = test_client.get(endpoint)
    assert response.json() == []


def _assert_reported_issue(value: dict, expected: dict) -> None:
    assert value["environment_name"] == expected["environment_name"]
    assert value["url"] == expected["url"]
    assert value["description"] == expected["description"]
    assert isinstance(value["id"], int)
    assert isinstance(value["created_at"], str)
    assert isinstance(value["updated_at"], str)
