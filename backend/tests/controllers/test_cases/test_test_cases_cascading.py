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

import uuid
from fastapi.testclient import TestClient

from tests.data_generator import DataGenerator
from tests.conftest import make_authenticated_request
from test_observer.data_access.models_enums import FamilyName
from test_observer.common.permissions import Permission


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
    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/test-cases?families=snap&q=test_{unique_marker}"),
        Permission.view_test,
    )

    assert response.status_code == 200
    test_cases = response.json()["test_cases"]
    test_case_names = [tc["test_case"] for tc in test_cases]

    # Should only include snap test case
    assert snap_test.name in test_case_names
    assert deb_test.name not in test_case_names
