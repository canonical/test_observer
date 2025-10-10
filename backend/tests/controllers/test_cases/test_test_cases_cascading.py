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
