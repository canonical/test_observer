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

from tests.data_generator import DataGenerator

attach_endpoint = "/v1/issues/{id}/attach"
detach_endpoint = "/v1/issues/{id}/detach"


def gen_test_results(generator: DataGenerator):
    environment = generator.gen_environment()
    test_case = generator.gen_test_case()
    artefact = generator.gen_artefact()
    artefact_build = generator.gen_artefact_build(artefact)
    test_execution = generator.gen_test_execution(artefact_build, environment)
    test_result_1 = generator.gen_test_result(test_case, test_execution)
    test_result_2 = generator.gen_test_result(test_case, test_execution)
    return test_result_1, test_result_2


def test_issue_attach_empty(test_client: TestClient, generator: DataGenerator):
    issue = generator.gen_issue()
    response = test_client.post(
        attach_endpoint.format(id=issue.id),
        json={"test_results": []},
    )
    assert response.json()["test_results"] == []


def test_issue_attach_one(test_client: TestClient, generator: DataGenerator):
    test_result = gen_test_results(generator)[0]
    issue = generator.gen_issue()
    response = test_client.post(
        attach_endpoint.format(id=issue.id), json={"test_results": [test_result.id]}
    )
    assert {
        attachment["test_result"]["id"]
        for attachment in response.json()["test_results"]
    } == {test_result.id}


def test_issue_attach_repeat(test_client: TestClient, generator: DataGenerator):
    test_result = gen_test_results(generator)[0]
    issue = generator.gen_issue()
    response = test_client.post(
        attach_endpoint.format(id=issue.id), json={"test_results": [test_result.id]}
    )
    response = test_client.post(
        attach_endpoint.format(id=issue.id), json={"test_results": [test_result.id]}
    )
    assert {
        attachment["test_result"]["id"]
        for attachment in response.json()["test_results"]
    } == {test_result.id}


def test_issue_attach_multiple(test_client: TestClient, generator: DataGenerator):
    test_results = gen_test_results(generator)
    issue = generator.gen_issue()
    response = test_client.post(
        attach_endpoint.format(id=issue.id), json={"test_results": [test_results[0].id]}
    )
    response = test_client.post(
        attach_endpoint.format(id=issue.id), json={"test_results": [test_results[1].id]}
    )
    assert {
        attachment["test_result"]["id"]
        for attachment in response.json()["test_results"]
    } == {test_results[0].id, test_results[1].id}


def test_issue_detach_one(test_client: TestClient, generator: DataGenerator):
    test_result = gen_test_results(generator)[0]
    issue = generator.gen_issue()
    response = test_client.post(
        attach_endpoint.format(id=issue.id), json={"test_results": [test_result.id]}
    )
    response = test_client.post(
        detach_endpoint.format(id=issue.id), json={"test_results": [test_result.id]}
    )
    assert response.json()["test_results"] == []


def test_issue_detach_repeat(test_client: TestClient, generator: DataGenerator):
    test_result = gen_test_results(generator)[0]
    issue = generator.gen_issue()
    response = test_client.post(
        attach_endpoint.format(id=issue.id), json={"test_results": [test_result.id]}
    )
    response = test_client.post(
        detach_endpoint.format(id=issue.id), json={"test_results": [test_result.id]}
    )
    response = test_client.post(
        detach_endpoint.format(id=issue.id), json={"test_results": [test_result.id]}
    )
    assert response.json()["test_results"] == []


def test_issue_detach_some(test_client: TestClient, generator: DataGenerator):
    test_results = gen_test_results(generator)
    issue = generator.gen_issue()
    response = test_client.post(
        attach_endpoint.format(id=issue.id),
        json={"test_results": [test_results[0].id, test_results[1].id]},
    )
    response = test_client.post(
        detach_endpoint.format(id=issue.id), json={"test_results": [test_results[0].id]}
    )
    assert {
        attachment["test_result"]["id"]
        for attachment in response.json()["test_results"]
    } == {test_results[1].id}
