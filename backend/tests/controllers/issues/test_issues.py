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


from fastapi.testclient import TestClient

from tests.asserts import assert_fails_validation

endpoint = "/v1/issues"
valid_post_data = {
    "url": "https://github.com/canonical/test_observer/issues/71",
    "title": "some title",
    "status": "open",
}
sample_issue_json = {
    "url": valid_post_data["url"],
    "title": valid_post_data["title"],
    "status": valid_post_data["status"],
    "source": "github",
    "project": "canonical/test_observer",
    "key": "71",
}

def test_empty_get_all(test_client: TestClient):
    response = test_client.get(endpoint)
    assert response.status_code == 200
    assert response.json() == {"issues": []}

def test_get_all(test_client: TestClient):
    post_response = test_client.post(endpoint, json=valid_post_data)
    response = test_client.get(endpoint)
    assert response.status_code == 200
    assert response.json() == {
        "issues": [{**sample_issue_json, "id": post_response.json()["id"]}],
    }

def test_get_issue(test_client: TestClient):
    post_response = test_client.post(endpoint, json=valid_post_data)
    response = test_client.get(endpoint + f"/{post_response.json()['id']}")
    assert response.status_code == 200
    assert response.json() == {**sample_issue_json, "id": post_response.json()["id"]}

def test_patch_invalid_status(test_client: TestClient):
    post_response = test_client.post(endpoint, json=valid_post_data)
    response = test_client.patch(endpoint + f"/{post_response.json()['id']}", json={
        "status": "unknown-status",
    })
    assert response.status_code == 422

def test_patch_no_change(test_client: TestClient):
    post_response = test_client.post(endpoint, json=valid_post_data)
    response = test_client.patch(endpoint + f"/{post_response.json()['id']}", json={})
    assert post_response.json() == response.json()

def test_patch_all(test_client: TestClient):
    post_response = test_client.post(endpoint, json=valid_post_data)
    response = test_client.patch(endpoint + f"/{post_response.json()['id']}", json={
        "title": "new title",
        "status": "closed",
    })
    assert response.json()["title"] == "new title"
    assert response.json()["status"] == "closed"

def test_post_requires_url(test_client: TestClient):
    response = test_client.post(endpoint, json={})
    assert_fails_validation(response, "url", "missing")

def test_post_indempotent(test_client: TestClient):
    test_client.post(endpoint, json=valid_post_data)
    test_client.post(endpoint, json=valid_post_data)
    response = test_client.get(endpoint)
    assert len(response.json()["issues"]) == 1

def test_post_update_existing(test_client: TestClient):
    test_client.post(endpoint, json=valid_post_data)
    test_client.post(endpoint, json={**valid_post_data, "title": "new title"})
    response = test_client.get(endpoint)
    assert response.json()["issues"][0]["title"] == "new title"

def test_post_invalid_url(test_client: TestClient):
    post_data = {**valid_post_data, "url": "http://unknown.com/bug/1"}
    response = test_client.post(endpoint, json=post_data)
    assert response.status_code == 422

def test_post_invalid_status(test_client: TestClient):
    post_data = {**valid_post_data, "status": "random"}
    response = test_client.post(endpoint, json=post_data)
    assert response.status_code == 422

def test_post_defaults(test_client: TestClient):
    post_data = {"url": valid_post_data["url"]}
    response = test_client.post(endpoint, json=post_data)
    assert response.json()["title"] == ""
    assert response.json()["status"] == "unknown"