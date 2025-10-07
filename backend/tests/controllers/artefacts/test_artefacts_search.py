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
from test_observer.common.permissions import Permission
from tests.data_generator import DataGenerator
from tests.conftest import make_authenticated_request


def generate_unique_name(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def test_search_artefacts_endpoint_exists(test_client: TestClient):
    """Test that the search endpoint exists and returns proper format"""
    response = make_authenticated_request(
        lambda: test_client.get("/v1/artefacts/search"),
        Permission.view_artefact,
    )
    assert response.status_code == 200
    data = response.json()
    assert "artefacts" in data
    assert isinstance(data["artefacts"], list)


def test_search_artefacts_no_query(test_client: TestClient, generator: DataGenerator):
    """Test searching without query returns all artefacts"""
    unique_marker = uuid.uuid4().hex[:8]
    artefact1 = generator.gen_artefact(name=f"test_artefact_1_{unique_marker}")
    artefact2 = generator.gen_artefact(name=f"test_artefact_2_{unique_marker}")

    response = make_authenticated_request(
        lambda: test_client.get("/v1/artefacts/search"),
        Permission.view_artefact,
    )

    assert response.status_code == 200
    data = response.json()
    artefacts = data["artefacts"]

    assert artefact1.name in artefacts
    assert artefact2.name in artefacts


def test_search_artefacts_with_query(test_client: TestClient, generator: DataGenerator):
    """Test searching with query filters results"""
    unique_marker = uuid.uuid4().hex[:8]

    target_artefact = generator.gen_artefact(name=f"special_search_{unique_marker}")
    other_artefact = generator.gen_artefact(name=f"other_artefact_{unique_marker}")

    # Search for the specific pattern
    response = make_authenticated_request(
        lambda: test_client.get("/v1/artefacts/search?q=special_search"),
        Permission.view_artefact,
    )

    assert response.status_code == 200
    data = response.json()
    artefacts = data["artefacts"]

    assert target_artefact.name in artefacts
    assert other_artefact.name not in artefacts


def test_search_artefacts_case_insensitive(
    test_client: TestClient, generator: DataGenerator
):
    """Test that search is case-insensitive"""
    unique_marker = uuid.uuid4().hex[:8]
    artefact_name = f"MixedCase_Artefact_{unique_marker}"

    generator.gen_artefact(name=artefact_name)

    for search_term in ["mixedcase", "MIXEDCASE", "MixedCase"]:
        response = make_authenticated_request(
            lambda url=f"/v1/artefacts/search?q={search_term}": test_client.get(url),
            Permission.view_artefact,
        )
        assert response.status_code == 200
        artefacts = response.json()["artefacts"]
        assert artefact_name in artefacts


def test_search_artefacts_partial_match(
    test_client: TestClient, generator: DataGenerator
):
    """Test that search supports partial matching"""
    unique_marker = uuid.uuid4().hex[:8]
    artefact_name = f"ubuntu_desktop_{unique_marker}"

    generator.gen_artefact(name=artefact_name)

    response = make_authenticated_request(
        lambda: test_client.get("/v1/artefacts/search?q=desktop"),
        Permission.view_artefact,
    )

    assert response.status_code == 200
    artefacts = response.json()["artefacts"]
    assert artefact_name in artefacts


def test_search_artefacts_pagination(test_client: TestClient, generator: DataGenerator):
    """Test that pagination works correctly"""
    unique_marker = uuid.uuid4().hex[:8]
    names = []

    for i in range(10):
        name = f"paginated_artefact_{unique_marker}_{i:02d}"
        generator.gen_artefact(name=name)
        names.append(name)

    expected_sorted = sorted(names)

    # Get first page
    response = make_authenticated_request(
        lambda: test_client.get(
            f"/v1/artefacts/search?q=paginated_artefact_{unique_marker}&limit=3&offset=0"
        ),
        Permission.view_artefact,
    )
    assert response.status_code == 200
    page1 = response.json()["artefacts"]
    assert len(page1) == 3
    assert page1 == expected_sorted[0:3]

    # Get second page
    response = make_authenticated_request(
        lambda: test_client.get(
            f"/v1/artefacts/search?q=paginated_artefact_{unique_marker}&limit=3&offset=3"
        ),
        Permission.view_artefact,
    )
    assert response.status_code == 200
    page2 = response.json()["artefacts"]
    assert len(page2) == 3
    assert page2 == expected_sorted[3:6]


def test_search_artefacts_limit_validation(test_client: TestClient):
    """Test that limit parameter is validated"""
    # Test maximum limit
    response = make_authenticated_request(
        lambda: test_client.get("/v1/artefacts/search?limit=1001"),
        Permission.view_artefact,
    )
    assert response.status_code == 422

    # Test minimum limit
    response = make_authenticated_request(
        lambda: test_client.get("/v1/artefacts/search?limit=0"),
        Permission.view_artefact,
    )
    assert response.status_code == 422


def test_search_artefacts_offset_validation(test_client: TestClient):
    """Test that offset parameter is validated"""
    # Test negative offset
    response = make_authenticated_request(
        lambda: test_client.get("/v1/artefacts/search?offset=-1"),
        Permission.view_artefact,
    )
    assert response.status_code == 422


def test_search_artefacts_empty_result(test_client: TestClient):
    """Test that search with no results returns empty list"""
    response = make_authenticated_request(
        lambda: test_client.get("/v1/artefacts/search?q=nonexistent_artefact_xyz_123"),
        Permission.view_artefact,
    )

    assert response.status_code == 200
    assert response.json()["artefacts"] == []


def test_search_artefacts_strips_whitespace(
    test_client: TestClient, generator: DataGenerator
):
    """Test that search query strips leading/trailing whitespace"""
    unique_marker = uuid.uuid4().hex[:8]
    artefact_name = f"whitespace_test_{unique_marker}"

    generator.gen_artefact(name=artefact_name)

    response = make_authenticated_request(
        lambda: test_client.get("/v1/artefacts/search?q=  whitespace_test  "),
        Permission.view_artefact,
    )
    assert response.status_code == 200
    artefacts = response.json()["artefacts"]
    assert artefact_name in artefacts


def test_search_artefacts_excludes_archived(
    test_client: TestClient, generator: DataGenerator
):
    """Test that archived artefacts are excluded from search"""
    unique_marker = uuid.uuid4().hex[:8]

    active_artefact = generator.gen_artefact(name=f"active_artefact_{unique_marker}")

    archived_artefact = generator.gen_artefact(
        name=f"archived_artefact_{unique_marker}", archived=True
    )

    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefacts/search?q=artefact_{unique_marker}"),
        Permission.view_artefact,
    )

    assert response.status_code == 200
    artefacts = response.json()["artefacts"]

    assert active_artefact.name in artefacts
    assert archived_artefact.name not in artefacts


def test_search_artefacts_default_limit(
    test_client: TestClient, generator: DataGenerator
):
    """Test that default limit is 50"""
    unique_marker = uuid.uuid4().hex[:8]

    for i in range(60):
        generator.gen_artefact(name=f"limit_test_{unique_marker}_{i:03d}")

    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefacts/search?q=limit_test_{unique_marker}"),
        Permission.view_artefact,
    )

    assert response.status_code == 200
    artefacts = response.json()["artefacts"]
    assert len(artefacts) <= 50
    assert len(artefacts) == 50
