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


import pytest

from fastapi.testclient import TestClient

from tests.data_generator import DataGenerator

from test_observer.data_access.models import TestExecution

post_endpoint = "/v1/test-executions/{id}/execution-metadata"
get_endpoint = post_endpoint


@pytest.fixture
def sample_test_executions(
    generator: DataGenerator,
) -> tuple[TestExecution, TestExecution]:
    environment = generator.gen_environment()
    artefact = generator.gen_artefact()
    artefact_build = generator.gen_artefact_build(artefact)
    test_execution_1 = generator.gen_test_execution(artefact_build, environment)
    test_execution_2 = generator.gen_test_execution(artefact_build, environment)
    return test_execution_1, test_execution_2


@pytest.fixture
def sample_execution_metadata() -> dict:
    return {
        "category1": [
            "value1",
            "value2",
        ],
        "category2": [
            "value1",
        ],
    }


def test_execution_metadata_add_empty(
    test_client: TestClient, sample_test_executions: tuple[TestExecution, TestExecution]
):
    response = test_client.post(
        post_endpoint.format(id=sample_test_executions[0].id),
        json={"execution_metadata": {}},
    )
    assert response.json()["execution_metadata"] == {}


def test_execution_metadata_add_some(
    test_client: TestClient,
    sample_test_executions: tuple[TestExecution, TestExecution],
    sample_execution_metadata: dict[str, list[str]],
):
    response = test_client.post(
        post_endpoint.format(id=sample_test_executions[0].id),
        json={"execution_metadata": sample_execution_metadata},
    )
    assert response.json()["execution_metadata"] == sample_execution_metadata


def test_execution_metadata_add_same_twice(
    test_client: TestClient,
    sample_test_executions: tuple[TestExecution, TestExecution],
    sample_execution_metadata: dict[str, list[str]],
):
    test_client.post(
        post_endpoint.format(id=sample_test_executions[0].id),
        json={"execution_metadata": sample_execution_metadata},
    )
    response = test_client.post(
        post_endpoint.format(id=sample_test_executions[0].id),
        json={"execution_metadata": sample_execution_metadata},
    )
    assert response.json()["execution_metadata"] == sample_execution_metadata


def test_execution_metadata_add_different(
    test_client: TestClient,
    sample_test_executions: tuple[TestExecution, TestExecution],
    sample_execution_metadata: dict[str, list[str]],
):
    test_client.post(
        post_endpoint.format(id=sample_test_executions[0].id),
        json={"execution_metadata": sample_execution_metadata},
    )
    response = test_client.post(
        post_endpoint.format(id=sample_test_executions[0].id),
        json={"execution_metadata": {"category3": ["value"]}},
    )
    assert response.json()["execution_metadata"] == {
        **sample_execution_metadata,
        "category3": ["value"],
    }
