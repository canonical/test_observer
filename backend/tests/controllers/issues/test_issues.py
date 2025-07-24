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
from tests.data_generator import DataGenerator

endpoint = "/v1/issues"
valid_put_data = {
    "url": "https://github.com/canonical/test_observer/issues/71",
    "title": "some title",
    "status": "open",
}


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
    environment = generator.gen_environment()
    test_case = generator.gen_test_case()
    artefact = generator.gen_artefact()
    artefact_build = generator.gen_artefact_build(artefact)
    test_execution = generator.gen_test_execution(artefact_build, environment)
    test_result = generator.gen_test_result(test_case, test_execution)
    issue = generator.gen_issue()
    response = test_client.post(
        f"/v1/issues/{issue.id}/attach", json={"test_results": [test_result.id]}
    )

    response = test_client.get(endpoint + f"/{issue.id}")

    assert response.status_code == 200
    assert response.json()["id"] == issue.id
    assert response.json()["source"] == issue.source
    assert response.json()["project"] == issue.project
    assert response.json()["key"] == issue.key
    assert response.json()["title"] == issue.title
    assert response.json()["status"] == issue.status
    assert response.json()["url"] == issue.url
    assert len(response.json()["test_results"]) == 1
    assert response.json()["test_results"][0]["test_result"]["id"] == test_result.id
    assert (
        response.json()["test_results"][0]["test_execution"]["id"] == test_execution.id
    )
    assert response.json()["test_results"][0]["artefact"]["id"] == artefact.id
    assert (
        response.json()["test_results"][0]["artefact_build"]["id"] == artefact_build.id
    )


def test_patch_invalid_status(test_client: TestClient):
    put_response = test_client.put(endpoint, json=valid_put_data)
    response = test_client.patch(
        endpoint + f"/{put_response.json()['id']}",
        json={
            "status": "unknown-status",
        },
    )
    assert response.status_code == 422


def test_patch_no_change(test_client: TestClient):
    put_response = test_client.put(endpoint, json=valid_put_data)
    response = test_client.patch(endpoint + f"/{put_response.json()['id']}", json={})
    assert put_response.json() == response.json()


def test_patch_all(test_client: TestClient):
    put_response = test_client.put(endpoint, json=valid_put_data)
    response = test_client.patch(
        endpoint + f"/{put_response.json()['id']}",
        json={
            "title": "new title",
            "status": "closed",
        },
    )
    assert response.json()["title"] == "new title"
    assert response.json()["status"] == "closed"


def test_put_requires_url(test_client: TestClient):
    response = test_client.put(endpoint, json={})
    assert_fails_validation(response, "url", "missing")


def test_put_indempotent(test_client: TestClient):
    test_client.put(endpoint, json=valid_put_data)
    test_client.put(endpoint, json=valid_put_data)
    response = test_client.get(endpoint)
    assert len(response.json()["issues"]) == 1


def test_put_update_existing(test_client: TestClient):
    test_client.put(endpoint, json=valid_put_data)
    test_client.put(endpoint, json={**valid_put_data, "title": "new title"})
    response = test_client.get(endpoint)
    assert response.json()["issues"][0]["title"] == "new title"


def test_put_invalid_url(test_client: TestClient):
    put_data = {**valid_put_data, "url": "http://unknown.com/bug/1"}
    response = test_client.put(endpoint, json=put_data)
    assert response.status_code == 422


def test_put_invalid_status(test_client: TestClient):
    put_data = {**valid_put_data, "status": "random"}
    response = test_client.put(endpoint, json=put_data)
    assert response.status_code == 422


def test_put_defaults(test_client: TestClient):
    put_data = {"url": valid_put_data["url"]}
    response = test_client.put(endpoint, json=put_data)
    assert response.json()["title"] == ""
    assert response.json()["status"] == "unknown"
