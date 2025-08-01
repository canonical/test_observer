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


def test_get_test_cases(test_client: TestClient):
    """Test getting test cases endpoint"""
    response = test_client.get("/v1/test-cases")

    assert response.status_code == 200
    data = response.json()
    assert "test_cases" in data
    assert isinstance(data["test_cases"], list)


def test_get_test_cases_invalid_family(test_client: TestClient):
    """Test invalid family returns 400"""
    response = test_client.get("/v1/test-cases?families=invalid_family")
    assert response.status_code == 400


def test_get_test_cases_response_format(test_client: TestClient):
    """Test response format"""
    response = test_client.get("/v1/test-cases")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "test_cases" in data
    assert isinstance(data["test_cases"], list)


def test_get_test_cases_with_actual_data(
    test_client: TestClient, generator: DataGenerator
):
    """Test that actual test cases are returned and properly validated"""
    # Create test data with specific test case
    environment = generator.gen_environment()
    test_case = generator.gen_test_case(
        name=generate_unique_name("validation_test"),
        template_id="validation_template_123",
    )
    artefact = generator.gen_artefact(name=generate_unique_name("validation_artefact"))
    artefact_build = generator.gen_artefact_build(artefact)
    test_execution = generator.gen_test_execution(artefact_build, environment)
    generator.gen_test_result(test_case, test_execution)

    response = test_client.get("/v1/test-cases")
    assert response.status_code == 200

    data = response.json()
    assert "test_cases" in data
    test_cases = data["test_cases"]
    assert isinstance(test_cases, list)

    # Find our specific test case in the flat list
    found_case = None
    for case in test_cases:
        if case["test_case"] == test_case.name:
            found_case = case
            break

    assert found_case is not None, f"Test case {test_case.name} not found in response"
    assert found_case["template_id"] == "validation_template_123"
    assert found_case["test_case"] == test_case.name


def test_get_test_cases_filtered_by_family(
    test_client: TestClient, generator: DataGenerator
):
    """Test filtering test cases by family"""
    # Create test data with snap family
    environment = generator.gen_environment()
    test_case = generator.gen_test_case(
        name=generate_unique_name("family_test"), template_id="family_template_456"
    )
    artefact = generator.gen_artefact(
        name=generate_unique_name("family_artefact"), family=FamilyName.snap
    )
    artefact_build = generator.gen_artefact_build(artefact)
    test_execution = generator.gen_test_execution(artefact_build, environment)
    generator.gen_test_result(test_case, test_execution)

    response = test_client.get("/v1/test-cases?families=snap")
    assert response.status_code == 200

    data = response.json()
    assert "test_cases" in data
    test_cases = data["test_cases"]
    assert isinstance(test_cases, list)

    # Verify our test case appears in the filtered results
    found_case = any(
        case["test_case"] == test_case.name
        and case["template_id"] == "family_template_456"
        for case in test_cases
    )
    assert found_case, (
        f"Test case {test_case.name} not found in family-filtered results"
    )


def test_get_test_cases_filtered_by_environment(
    test_client: TestClient, generator: DataGenerator
):
    """Test filtering test cases by environment"""
    # Create test data with specific environment
    unique_env_name = f"specific_env_{uuid.uuid4().hex[:8]}"
    environment = generator.gen_environment(name=unique_env_name)
    test_case = generator.gen_test_case(
        name=generate_unique_name("env_test"), template_id="env_template_789"
    )
    artefact = generator.gen_artefact(name=generate_unique_name("env_artefact"))
    artefact_build = generator.gen_artefact_build(artefact)
    test_execution = generator.gen_test_execution(artefact_build, environment)
    generator.gen_test_result(test_case, test_execution)

    response = test_client.get(f"/v1/test-cases?environments={unique_env_name}")
    assert response.status_code == 200

    data = response.json()
    test_cases = data["test_cases"]

    # Verify our test case appears in the environment-filtered results
    found_case = any(
        case["test_case"] == test_case.name
        and case["template_id"] == "env_template_789"
        for case in test_cases
    )
    assert found_case, (
        f"Test case {test_case.name} not found in environment-filtered results"
    )


def test_get_test_cases_combined_filters(
    test_client: TestClient, generator: DataGenerator
):
    """Test filtering test cases by both family and environment"""
    # Create test data with both filters
    unique_env_name = f"combined_env_{uuid.uuid4().hex[:8]}"
    environment = generator.gen_environment(name=unique_env_name)
    test_case = generator.gen_test_case(
        name=generate_unique_name("combined_test"), template_id="combined_template_999"
    )
    snap_artefact = generator.gen_artefact(
        name=generate_unique_name("combined_artefact"), family=FamilyName.snap
    )
    artefact_build = generator.gen_artefact_build(snap_artefact)
    test_execution = generator.gen_test_execution(artefact_build, environment)
    generator.gen_test_result(test_case, test_execution)

    response = test_client.get(
        f"/v1/test-cases?families=snap&environments={unique_env_name}"
    )
    assert response.status_code == 200

    data = response.json()
    test_cases = data["test_cases"]

    # Verify our test case appears with both filters applied
    found_case = any(
        case["test_case"] == test_case.name
        and case["template_id"] == "combined_template_999"
        for case in test_cases
    )
    assert found_case, (
        f"Test case {test_case.name} not found in combined-filtered results"
    )


def test_get_test_cases_empty_template_id(
    test_client: TestClient, generator: DataGenerator
):
    """Test test cases with empty template_id are handled properly"""
    # Create test data with no template_id
    environment = generator.gen_environment()
    test_case = generator.gen_test_case(
        name=generate_unique_name("no_template_test"),
        template_id="",  # Empty template ID
    )
    artefact = generator.gen_artefact(name=generate_unique_name("no_template_artefact"))
    artefact_build = generator.gen_artefact_build(artefact)
    test_execution = generator.gen_test_execution(artefact_build, environment)
    generator.gen_test_result(test_case, test_execution)

    response = test_client.get("/v1/test-cases")
    assert response.status_code == 200

    data = response.json()
    test_cases = data["test_cases"]

    # Verify test case with empty template_id is included
    found_case = any(
        case["test_case"] == test_case.name and case["template_id"] == ""
        for case in test_cases
    )
    assert found_case, f"Test case {test_case.name} with empty template_id not found"
