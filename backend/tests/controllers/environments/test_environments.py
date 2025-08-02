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
from test_observer.data_access.models_enums import FamilyName


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


def test_get_environments_filtered_by_family(
    test_client: TestClient, generator: DataGenerator
):
    """Test cascading filter: environments filtered by family"""
    # Create test data with snap family
    unique_env_name = f"snap_only_env_{uuid.uuid4().hex[:8]}"
    environment = generator.gen_environment(name=unique_env_name)
    test_case = generator.gen_test_case(name=generate_unique_name("snap_env_test"))
    snap_artefact = generator.gen_artefact(
        name=generate_unique_name("snap_artefact"), family=FamilyName.snap
    )
    artefact_build = generator.gen_artefact_build(snap_artefact)
    test_execution = generator.gen_test_execution(artefact_build, environment)
    generator.gen_test_result(test_case, test_execution)

    # Create test data with deb family in different environment
    deb_env_name = f"deb_only_env_{uuid.uuid4().hex[:8]}"
    deb_environment = generator.gen_environment(name=deb_env_name)
    deb_test_case = generator.gen_test_case(name=generate_unique_name("deb_env_test"))
    deb_artefact = generator.gen_artefact(
        name=generate_unique_name("deb_artefact"), family=FamilyName.deb
    )
    deb_artefact_build = generator.gen_artefact_build(deb_artefact)
    deb_test_execution = generator.gen_test_execution(
        deb_artefact_build, deb_environment
    )
    generator.gen_test_result(deb_test_case, deb_test_execution)

    # Filter by snap family - should only include snap environment
    response = test_client.get("/v1/environments?families=snap")
    assert response.status_code == 200

    data = response.json()
    environments = data["environments"]

    # Should include snap environment but not deb environment
    assert unique_env_name in environments
    assert deb_env_name not in environments


def test_get_environments_filtered_by_test_case(
    test_client: TestClient, generator: DataGenerator
):
    """Test cascading filter: environments filtered by test case"""
    # Create test data with specific test case
    unique_env_name = f"specific_test_env_{uuid.uuid4().hex[:8]}"
    specific_test_name = generate_unique_name("very_specific_test_case")

    environment = generator.gen_environment(name=unique_env_name)
    test_case = generator.gen_test_case(name=specific_test_name)
    artefact = generator.gen_artefact(name=generate_unique_name("test_case_artefact"))
    artefact_build = generator.gen_artefact_build(artefact)
    test_execution = generator.gen_test_execution(artefact_build, environment)
    generator.gen_test_result(test_case, test_execution)

    # Filter by test case name
    response = test_client.get(f"/v1/environments?test_cases={specific_test_name}")
    assert response.status_code == 200

    data = response.json()
    environments = data["environments"]

    # Should include our specific environment
    assert unique_env_name in environments


def test_get_environments_filtered_by_partial_test_case(
    test_client: TestClient, generator: DataGenerator
):
    """Test cascading filter: environments filtered by partial test case match"""
    unique_env_name = f"partial_test_env_{uuid.uuid4().hex[:8]}"
    test_name_with_deploy = f"test_deploy_special_case_{uuid.uuid4().hex[:4]}"

    environment = generator.gen_environment(name=unique_env_name)
    test_case = generator.gen_test_case(name=test_name_with_deploy)
    artefact = generator.gen_artefact(name=generate_unique_name("deploy_artefact"))
    artefact_build = generator.gen_artefact_build(artefact)
    test_execution = generator.gen_test_execution(artefact_build, environment)
    generator.gen_test_result(test_case, test_execution)

    # Filter by partial test case name
    response = test_client.get("/v1/environments?test_cases=deploy")
    assert response.status_code == 200

    data = response.json()
    environments = data["environments"]

    # Should include our environment since test case contains "deploy"
    assert unique_env_name in environments


def test_get_environments_combined_filters(
    test_client: TestClient, generator: DataGenerator
):
    """Test cascading filter: environments filtered by both family and test case"""
    unique_env_name = f"combined_filter_env_{uuid.uuid4().hex[:8]}"
    specific_test_name = generate_unique_name("combined_filter_test")

    environment = generator.gen_environment(name=unique_env_name)
    test_case = generator.gen_test_case(name=specific_test_name)
    snap_artefact = generator.gen_artefact(
        name=generate_unique_name("combined_snap_artefact"), family=FamilyName.snap
    )
    artefact_build = generator.gen_artefact_build(snap_artefact)
    test_execution = generator.gen_test_execution(artefact_build, environment)
    generator.gen_test_result(test_case, test_execution)

    # Filter by both family and test case
    response = test_client.get(
        f"/v1/environments?families=snap&test_cases={specific_test_name}"
    )
    assert response.status_code == 200

    data = response.json()
    environments = data["environments"]

    # Should include our environment since it matches both filters
    assert unique_env_name in environments


def test_get_environments_invalid_family(test_client: TestClient):
    """Test invalid family parameter returns 400"""
    response = test_client.get("/v1/environments?families=invalid_family")
    assert response.status_code == 400
