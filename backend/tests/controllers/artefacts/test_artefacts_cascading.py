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


def test_artefacts_filter_by_family(test_client: TestClient, generator: DataGenerator):
    """Test that artefacts can be filtered by family"""
    unique_marker = uuid.uuid4().hex[:8]

    # Create snap and deb artefacts
    snap_artefact = generator.gen_artefact(
        family=FamilyName.snap, name=f"snap_artefact_{unique_marker}"
    )
    deb_artefact = generator.gen_artefact(
        family=FamilyName.deb, name=f"deb_artefact_{unique_marker}"
    )

    # Search for only snap family
    response = test_client.get(
        f"/v1/artefacts/search?families=snap&q=artefact_{unique_marker}"
    )

    assert response.status_code == 200
    artefacts = response.json()["artefacts"]

    # Should only include snap artefact
    assert snap_artefact.name in artefacts
    assert deb_artefact.name not in artefacts


def test_artefacts_filter_by_multiple_families(
    test_client: TestClient, generator: DataGenerator
):
    """Test that artefacts can be filtered by multiple families"""
    unique_marker = uuid.uuid4().hex[:8]

    snap_artefact = generator.gen_artefact(
        family=FamilyName.snap, name=f"snap_{unique_marker}"
    )
    deb_artefact = generator.gen_artefact(
        family=FamilyName.deb, name=f"deb_{unique_marker}"
    )
    charm_artefact = generator.gen_artefact(
        family=FamilyName.charm, name=f"charm_{unique_marker}"
    )

    # Search for snap and deb families
    response = test_client.get("/v1/artefacts/search?families=snap&families=deb")

    assert response.status_code == 200
    artefacts = response.json()["artefacts"]

    # Should include snap and deb, but not charm
    assert snap_artefact.name in artefacts
    assert deb_artefact.name in artefacts
    assert charm_artefact.name not in artefacts


def test_environments_filter_by_family(
    test_client: TestClient, generator: DataGenerator
):
    """Test that environments are filtered by family"""
    unique_marker = uuid.uuid4().hex[:8]

    # Create environments
    snap_env = generator.gen_environment(name=f"snap_env_{unique_marker}")
    deb_env = generator.gen_environment(name=f"deb_env_{unique_marker}")

    # Create snap artefact and test execution on snap_env
    snap_artefact = generator.gen_artefact(family=FamilyName.snap)
    snap_build = generator.gen_artefact_build(snap_artefact)
    test_case = generator.gen_test_case()
    snap_execution = generator.gen_test_execution(snap_build, snap_env)
    generator.gen_test_result(test_case, snap_execution)

    # Create deb artefact and test execution on deb_env
    deb_artefact = generator.gen_artefact(family=FamilyName.deb)
    deb_build = generator.gen_artefact_build(deb_artefact)
    deb_execution = generator.gen_test_execution(deb_build, deb_env)
    generator.gen_test_result(test_case, deb_execution)

    # Filter environments by snap family
    response = test_client.get(f"/v1/environments?families=snap&q=env_{unique_marker}")

    assert response.status_code == 200
    environments = response.json()["environments"]

    # Should only include snap environment
    assert snap_env.name in environments
    assert deb_env.name not in environments


def test_test_cases_filter_by_family(test_client: TestClient, generator: DataGenerator):
    """Test that test cases are filtered by family"""
    unique_marker = uuid.uuid4().hex[:8]

    # Create test cases
    snap_test = generator.gen_test_case(name=f"snap_test_{unique_marker}")
    deb_test = generator.gen_test_case(name=f"deb_test_{unique_marker}")

    # Create snap artefact and test execution with snap_test
    snap_artefact = generator.gen_artefact(family=FamilyName.snap)
    snap_build = generator.gen_artefact_build(snap_artefact)
    snap_env = generator.gen_environment(name=f"snap_test_env_{unique_marker}")
    snap_execution = generator.gen_test_execution(snap_build, snap_env)
    generator.gen_test_result(snap_test, snap_execution)

    # Create deb artefact and test execution with deb_test
    deb_artefact = generator.gen_artefact(family=FamilyName.deb)
    deb_build = generator.gen_artefact_build(deb_artefact)
    deb_env = generator.gen_environment(name=f"deb_test_env_{unique_marker}")
    deb_execution = generator.gen_test_execution(deb_build, deb_env)
    generator.gen_test_result(deb_test, deb_execution)

    # Filter test cases by snap family
    response = test_client.get(f"/v1/test-cases?families=snap&q=test_{unique_marker}")

    assert response.status_code == 200
    test_cases = response.json()["test_cases"]
    test_case_names = [tc["test_case"] for tc in test_cases]

    # Should only include snap test case
    assert snap_test.name in test_case_names
    assert deb_test.name not in test_case_names
