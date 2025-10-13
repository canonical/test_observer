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
from tests.conftest import make_authenticated_request
from test_observer.data_access.models_enums import FamilyName
from test_observer.common.permissions import Permission


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
    response = make_authenticated_request(
        lambda: test_client.get(
            f"/v1/environments?families=snap&q=env_{unique_marker}"
        ),
        Permission.view_test,
    )

    assert response.status_code == 200
    environments = response.json()["environments"]

    # Should only include snap environment
    assert snap_env.name in environments
    assert deb_env.name not in environments
