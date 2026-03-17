# Copyright 2025 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import pytest
from fastapi.testclient import TestClient

from test_observer.common.permissions import Permission
from test_observer.data_access.models import TestExecution
from tests.conftest import make_authenticated_request
from tests.data_generator import DataGenerator

test_executions_patch_endpoint = "/v1/test-executions/{id}"
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
    response = make_authenticated_request(
        lambda: test_client.get(get_endpoint),
        Permission.view_test,
    )
    assert response.json() == {"execution_metadata": {}}


def test_execution_metadata_get_all(
    test_client: TestClient,
    sample_test_executions: tuple[TestExecution, TestExecution],
):
    make_authenticated_request(
        lambda: test_client.patch(
            test_executions_patch_endpoint.format(id=sample_test_executions[0].id),
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
        ),
        Permission.change_test,
    )
    make_authenticated_request(
        lambda: test_client.patch(
            test_executions_patch_endpoint.format(id=sample_test_executions[0].id),
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
        ),
        Permission.change_test,
    )
    response = make_authenticated_request(
        lambda: test_client.get(get_endpoint),
        Permission.view_test,
    )
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
