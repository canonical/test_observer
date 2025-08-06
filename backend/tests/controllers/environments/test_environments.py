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

import uuid
from fastapi.testclient import TestClient
from tests.data_generator import DataGenerator


def generate_unique_name(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def test_get_environments(test_client: TestClient):
    """Test getting environments endpoint"""
    response = test_client.get("/v1/environments")

    assert response.status_code == 200
    data = response.json()
    assert "environments" in data
    assert isinstance(data["environments"], list)


def test_get_environments_response_format(test_client: TestClient):
    """Test response format"""
    response = test_client.get("/v1/environments")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "environments" in data


def test_create_environment_and_validate_returned(
    test_client: TestClient, generator: DataGenerator
):
    """Test that creates an environment and validates it is returned in the response"""
    # Create a unique environment name to ensure we can find it
    unique_env_name = f"test_validation_env_{uuid.uuid4().hex[:8]}"

    # Create test data with the specific environment
    environment = generator.gen_environment(name=unique_env_name)
    test_case = generator.gen_test_case(
        name=generate_unique_name("env_validation_test")
    )
    artefact = generator.gen_artefact(
        name=generate_unique_name("env_validation_artefact")
    )
    artefact_build = generator.gen_artefact_build(artefact)
    test_execution = generator.gen_test_execution(artefact_build, environment)
    # Create test result to ensure the environment appears in queries
    generator.gen_test_result(test_case, test_execution)

    # Get environments and verify our created environment is included
    response = test_client.get("/v1/environments")

    assert response.status_code == 200
    data = response.json()
    assert "environments" in data
    environments = data["environments"]
    assert isinstance(environments, list)

    # Verify our specific environment is in the response
    assert unique_env_name in environments, (
        f"Environment {unique_env_name} not found in response: {environments}"
    )
