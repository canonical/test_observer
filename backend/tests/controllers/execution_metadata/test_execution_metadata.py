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

test_executions_post_endpoint = "/v1/test-executions/{id}/execution-metadata"
get_endpoint = "/v1/execution-metadata"


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


def test_execution_metadata_get_empty(test_client: TestClient):
    response = test_client.get(get_endpoint)
    assert response.json() == {"execution_metadata": {}}


def test_execution_metadata_get_all(
    test_client: TestClient,
    sample_test_executions: tuple[TestExecution, TestExecution],
):
    test_client.post(
        test_executions_post_endpoint.format(id=sample_test_executions[0].id),
        json={
            "execution_metadata": {
                "category1": [
                    "value1",
                    "value2",
                ],
                "category2": [
                    "value1",
                ],
            }
        },
    )
    test_client.post(
        test_executions_post_endpoint.format(id=sample_test_executions[0].id),
        json={
            "execution_metadata": {
                "category2": [
                    "value2",
                ],
                "category3": [
                    "value1",
                    "value2",
                ],
            }
        },
    )
    response = test_client.get(get_endpoint)
    assert response.json() == {
        "execution_metadata": {
            "category1": [
                "value1",
                "value2",
            ],
            "category2": [
                "value1",
                "value2",
            ],
            "category3": [
                "value1",
                "value2",
            ],
        }
    }
