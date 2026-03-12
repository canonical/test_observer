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

from test_observer.common.permissions import Permission
from test_observer.data_access.models_enums import FamilyName
from tests.conftest import make_authenticated_request
from tests.data_generator import DataGenerator


def generate_unique_name(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def test_artefacts_filter_by_family(test_client: TestClient, generator: DataGenerator):
    """Test that artefacts can be filtered by family"""
    unique_marker = uuid.uuid4().hex[:8]

    # Create snap and deb artefacts
    snap_artefact = generator.gen_artefact(family=FamilyName.snap, name=f"snap_artefact_{unique_marker}")
    deb_artefact = generator.gen_artefact(family=FamilyName.deb, name=f"deb_artefact_{unique_marker}")

    # Search for only snap family
    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefacts/search?families=snap&q=artefact_{unique_marker}"),
        Permission.view_artefact,
    )

    assert response.status_code == 200
    artefacts = response.json()["artefacts"]

    # Should only include snap artefact
    assert snap_artefact.name in artefacts
    assert deb_artefact.name not in artefacts


def test_artefacts_filter_by_multiple_families(test_client: TestClient, generator: DataGenerator):
    """Test that artefacts can be filtered by multiple families"""
    unique_marker = uuid.uuid4().hex[:8]

    snap_artefact = generator.gen_artefact(family=FamilyName.snap, name=f"snap_{unique_marker}")
    deb_artefact = generator.gen_artefact(family=FamilyName.deb, name=f"deb_{unique_marker}")
    charm_artefact = generator.gen_artefact(family=FamilyName.charm, name=f"charm_{unique_marker}")

    # Search for snap and deb families
    response = make_authenticated_request(
        lambda: test_client.get("/v1/artefacts/search?families=snap&families=deb"),
        Permission.view_artefact,
    )

    assert response.status_code == 200
    artefacts = response.json()["artefacts"]

    # Should include snap and deb, but not charm
    assert snap_artefact.name in artefacts
    assert deb_artefact.name in artefacts
    assert charm_artefact.name not in artefacts
