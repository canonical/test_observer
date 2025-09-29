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
from tests.conftest import make_authenticated_request
from tests.data_generator import DataGenerator
from test_observer.common.permissions import Permission

endpoint = "/v1/issues"
valid_put_data = {
    "url": "https://github.com/canonical/test_observer/issues/71",
    "title": "some title",
    "status": "open",
}


def auth_request(method: str, test_client: TestClient, endpoint: str, **kwargs):
    return make_authenticated_request(
        lambda: getattr(test_client, method)(endpoint, **kwargs),
        Permission.change_issue,
    )


def test_empty_get_all(test_client: TestClient):
    response = test_client.get(endpoint)
    assert response.status_code == 200
    assert response.json() == {"issues": []}


def test_get_all(test_client: TestClient, generator: DataGenerator):
    issue = generator.gen_issue()

    response = test_client.get(endpoint)

    assert response.status_code == 200
    assert response.json() == {
        "issues": [
            {
                "id": issue.id,
                "source": issue.source,
                "project": issue.project,
                "key": issue.key,
                "title": issue.title,
                "status": issue.status,
                "url": issue.url,
            }
        ],
    }


def test_get_issue(test_client: TestClient, generator: DataGenerator):
    issue = generator.gen_issue()

    response = test_client.get(endpoint + f"/{issue.id}")

    assert response.status_code == 200
    assert set(response.json().keys()) == {
        "attachment_rules",
        "url",
        "key",
        "id",
        "project",
        "source",
        "title",
        "status",
    }
    assert response.json()["id"] == issue.id
    assert response.json()["source"] == issue.source
    assert response.json()["project"] == issue.project
    assert response.json()["key"] == issue.key
    assert response.json()["title"] == issue.title
    assert response.json()["status"] == issue.status
    assert response.json()["url"] == issue.url


def test_patch_invalid_status(test_client: TestClient):
    put_response = auth_request("put", test_client, endpoint, json=valid_put_data)
    response = auth_request(
        "patch",
        test_client,
        endpoint + f"/{put_response.json()['id']}",
        json={"status": "unknown-status"},
    )
    assert response.status_code == 422


def test_patch_no_change(test_client: TestClient):
    put_response = auth_request("put", test_client, endpoint, json=valid_put_data)
    response = auth_request(
        "patch", test_client, endpoint + f"/{put_response.json()['id']}", json={}
    )
    assert put_response.json() == response.json()


def test_patch_all(test_client: TestClient):
    put_response = auth_request("put", test_client, endpoint, json=valid_put_data)
    response = auth_request(
        "patch",
        test_client,
        endpoint + f"/{put_response.json()['id']}",
        json={"title": "new title", "status": "closed"},
    )
    assert response.json()["title"] == "new title"
    assert response.json()["status"] == "closed"


def test_put_requires_url(test_client: TestClient):
    response = auth_request("put", test_client, endpoint, json={})
    assert_fails_validation(response, "url", "missing")


def test_put_indempotent(test_client: TestClient):
    auth_request("put", test_client, endpoint, json=valid_put_data)
    auth_request("put", test_client, endpoint, json=valid_put_data)
    response = test_client.get(endpoint)
    assert len(response.json()["issues"]) == 1


def test_put_update_existing(test_client: TestClient):
    auth_request("put", test_client, endpoint, json=valid_put_data)
    auth_request(
        "put", test_client, endpoint, json={**valid_put_data, "title": "new title"}
    )
    response = test_client.get(endpoint)
    assert response.json()["issues"][0]["title"] == "new title"


def test_put_invalid_url(test_client: TestClient):
    put_data = {**valid_put_data, "url": "http://unknown.com/bug/1"}
    response = auth_request("put", test_client, endpoint, json=put_data)
    assert response.status_code == 422


def test_put_invalid_status(test_client: TestClient):
    put_data = {**valid_put_data, "status": "random"}
    response = auth_request("put", test_client, endpoint, json=put_data)
    assert response.status_code == 422


def test_put_defaults(test_client: TestClient):
    put_data = {"url": valid_put_data["url"]}
    response = auth_request("put", test_client, endpoint, json=put_data)
    assert response.json()["title"] == ""
    assert response.json()["status"] == "unknown"
