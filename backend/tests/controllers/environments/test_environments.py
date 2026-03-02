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
from tests.conftest import make_authenticated_request
from tests.data_generator import DataGenerator


def generate_unique_name(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _seed_environments(generator: DataGenerator, count: int, prefix: str = "test_env") -> list[str]:
    """
    Helper to create test environments with test results.
    Creates its own artefact build for each environment.
    """
    art = generator.gen_artefact(name=generate_unique_name("artefact"))
    art_build = generator.gen_artefact_build(art)
    test_case = generator.gen_test_case(name=generate_unique_name("test_case"))

    names: list[str] = []
    for i in range(count):
        name = f"{prefix}_{i:03d}_{uuid.uuid4().hex[:6]}"
        env = generator.gen_environment(name=name)
        te = generator.gen_test_execution(art_build, env)
        generator.gen_test_result(test_case, te)
        names.append(name)
    return names


def test_get_environments(test_client: TestClient):
    """Test getting environments endpoint"""
    response = make_authenticated_request(
        lambda: test_client.get("/v1/environments"),
        Permission.view_test,
    )

    assert response.status_code == 200
    data = response.json()
    assert "environments" in data
    assert isinstance(data["environments"], list)


def test_get_environments_response_format(test_client: TestClient):
    """Test response format"""
    response = make_authenticated_request(
        lambda: test_client.get("/v1/environments"),
        Permission.view_test,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "environments" in data


def test_create_environment_and_validate_returned(test_client: TestClient, generator: DataGenerator):
    """Test that creates an environment and validates it is returned in the response"""
    # Create a unique environment name to ensure we can find it
    unique_env_name = f"test_validation_env_{uuid.uuid4().hex[:8]}"

    # Create test data with the specific environment
    environment = generator.gen_environment(name=unique_env_name)
    test_case = generator.gen_test_case(name=generate_unique_name("env_validation_test"))
    artefact = generator.gen_artefact(name=generate_unique_name("env_validation_artefact"))
    artefact_build = generator.gen_artefact_build(artefact)
    test_execution = generator.gen_test_execution(artefact_build, environment)
    # Create test result to ensure the environment appears in queries
    generator.gen_test_result(test_case, test_execution)

    # Get environments and verify our created environment is included
    response = make_authenticated_request(
        lambda: test_client.get("/v1/environments"),
        Permission.view_test,
    )

    assert response.status_code == 200
    data = response.json()
    assert "environments" in data
    environments = data["environments"]
    assert isinstance(environments, list)

    # Verify our specific environment is in the response
    assert unique_env_name in environments, f"Environment {unique_env_name} not found in response: {environments}"


def test_default_limit_is_50(test_client: TestClient, generator: DataGenerator):
    """When no limit is passed, endpoint should return up to 50 results."""
    _seed_environments(generator, 60, prefix="default_limit")
    resp = make_authenticated_request(
        lambda: test_client.get("/v1/environments"),
        Permission.view_test,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "environments" in data
    assert len(data["environments"]) <= 50
    assert len(data["environments"]) == 50  # exactly 50 when >=50 exist


def test_explicit_limit_and_offset_window(test_client: TestClient, generator: DataGenerator):
    """
    Verify limit/offset produce expected window with deterministic
    ordering by name.
    """
    names = _seed_environments(generator, 20, prefix="window_check")
    expected_sorted = sorted(names)

    resp = make_authenticated_request(
        lambda: test_client.get("/v1/environments", params={"limit": 5, "offset": 5}),
        Permission.view_test,
    )
    assert resp.status_code == 200
    got = resp.json()["environments"]
    assert len(got) == 5
    assert got == expected_sorted[5:10]


def test_search_filter_q_ilike(test_client: TestClient, generator: DataGenerator):
    """Search should filter by name (ILIKE)."""
    # Create environments with specific patterns
    art = generator.gen_artefact(name=generate_unique_name("artefact"))
    art_build = generator.gen_artefact_build(art)
    test_case = generator.gen_test_case(name=generate_unique_name("test_case"))

    unique_marker = uuid.uuid4().hex[:8]
    target_name = f"special_search_{unique_marker}"
    other_name1 = f"other_env_{unique_marker}_1"
    other_name2 = f"other_env_{unique_marker}_2"

    for name in [target_name, other_name1, other_name2]:
        env = generator.gen_environment(name=name)
        te = generator.gen_test_execution(art_build, env)
        generator.gen_test_result(test_case, te)

    # Search for the specific pattern
    resp = make_authenticated_request(
        lambda: test_client.get("/v1/environments", params={"q": "special_search"}),
        Permission.view_test,
    )
    assert resp.status_code == 200
    got_environments = resp.json()["environments"]

    # Should only find the target environment
    assert target_name in got_environments
    assert other_name1 not in got_environments
    assert other_name2 not in got_environments


def test_search_case_insensitive(test_client: TestClient, generator: DataGenerator):
    """Search should be case-insensitive."""
    art = generator.gen_artefact(name=generate_unique_name("artefact"))
    art_build = generator.gen_artefact_build(art)
    test_case = generator.gen_test_case(name=generate_unique_name("test_case"))

    unique_marker = uuid.uuid4().hex[:8]
    env_name = f"MixedCase_Environment_{unique_marker}"

    env = generator.gen_environment(name=env_name)
    te = generator.gen_test_execution(art_build, env)
    generator.gen_test_result(test_case, te)

    # Search with different cases
    for search_term in ["mixedcase", "MIXEDCASE", "MixedCase"]:
        resp = make_authenticated_request(
            lambda: test_client.get("/v1/environments", params={"q": search_term}),  # noqa: B023
            Permission.view_test,
        )
        assert resp.status_code == 200
        got_environments = resp.json()["environments"]
        assert env_name in got_environments


def test_search_partial_match(test_client: TestClient, generator: DataGenerator):
    """Search should support partial matching."""
    art = generator.gen_artefact(name=generate_unique_name("artefact"))
    art_build = generator.gen_artefact_build(art)
    test_case = generator.gen_test_case(name=generate_unique_name("test_case"))

    unique_marker = uuid.uuid4().hex[:8]
    env_name = f"production_server_{unique_marker}"

    env = generator.gen_environment(name=env_name)
    te = generator.gen_test_execution(art_build, env)
    generator.gen_test_result(test_case, te)

    # Search with partial term
    resp = make_authenticated_request(
        lambda: test_client.get("/v1/environments", params={"q": "production"}),
        Permission.view_test,
    )
    assert resp.status_code == 200
    got_environments = resp.json()["environments"]
    assert env_name in got_environments


def test_search_with_pagination(test_client: TestClient, generator: DataGenerator):
    """Search results should respect pagination parameters."""
    names = []
    art = generator.gen_artefact(name=generate_unique_name("artefact"))
    art_build = generator.gen_artefact_build(art)
    test_case = generator.gen_test_case(name=generate_unique_name("test_case"))

    # Create 10 environments with common prefix
    unique_marker = uuid.uuid4().hex[:8]
    for i in range(10):
        name = f"paginated_env_{unique_marker}_{i:02d}"
        names.append(name)
        env = generator.gen_environment(name=name)
        te = generator.gen_test_execution(art_build, env)
        generator.gen_test_result(test_case, te)

    expected_sorted = sorted(names)

    # Get first page
    resp = make_authenticated_request(
        lambda: test_client.get(
            "/v1/environments",
            params={"q": f"paginated_env_{unique_marker}", "limit": 3, "offset": 0},
        ),
        Permission.view_test,
    )
    assert resp.status_code == 200
    page1 = resp.json()["environments"]
    assert len(page1) == 3
    assert page1 == expected_sorted[0:3]

    # Get second page
    resp = make_authenticated_request(
        lambda: test_client.get(
            "/v1/environments",
            params={"q": f"paginated_env_{unique_marker}", "limit": 3, "offset": 3},
        ),
        Permission.view_test,
    )
    assert resp.status_code == 200
    page2 = resp.json()["environments"]
    assert len(page2) == 3
    assert page2 == expected_sorted[3:6]


def test_pagination_limits(test_client: TestClient):
    """Test pagination parameter validation"""
    # Test maximum limit
    response = make_authenticated_request(
        lambda: test_client.get("/v1/environments?limit=1001"),
        Permission.view_test,
    )
    assert response.status_code == 422

    # Test negative offset
    response = make_authenticated_request(
        lambda: test_client.get("/v1/environments?offset=-1"),
        Permission.view_test,
    )
    assert response.status_code == 422

    # Test minimum limit
    response = make_authenticated_request(
        lambda: test_client.get("/v1/environments?limit=0"),
        Permission.view_test,
    )
    assert response.status_code == 422


def test_empty_search_returns_empty_list(test_client: TestClient):
    """Test search with no results returns empty list."""
    resp = make_authenticated_request(
        lambda: test_client.get("/v1/environments", params={"q": "nonexistent_environment_xyz_123"}),
        Permission.view_test,
    )
    assert resp.status_code == 200
    assert resp.json()["environments"] == []


def test_search_strips_whitespace(test_client: TestClient, generator: DataGenerator):
    """Test that search query strips leading/trailing whitespace."""
    art = generator.gen_artefact(name=generate_unique_name("artefact"))
    art_build = generator.gen_artefact_build(art)
    test_case = generator.gen_test_case(name=generate_unique_name("test_case"))

    unique_marker = uuid.uuid4().hex[:8]
    env_name = f"whitespace_test_{unique_marker}"

    env = generator.gen_environment(name=env_name)
    te = generator.gen_test_execution(art_build, env)
    generator.gen_test_result(test_case, te)

    # Search with extra whitespace
    resp = make_authenticated_request(
        lambda: test_client.get("/v1/environments", params={"q": "  whitespace_test  "}),
        Permission.view_test,
    )
    assert resp.status_code == 200
    got_environments = resp.json()["environments"]
    assert env_name in got_environments


def test_get_environments_pagination_metadata(test_client: TestClient, generator: DataGenerator):
    """count reflects total results, limit and offset echo back the used values"""
    unique_marker = uuid.uuid4().hex[:8]
    _ = _seed_environments(generator, count=5, prefix=f"meta_env_{unique_marker}")

    resp = make_authenticated_request(
        lambda: test_client.get(
            "/v1/environments",
            params={"q": f"meta_env_{unique_marker}", "limit": 2, "offset": 1},
        ),
        Permission.view_test,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 1
    assert len(data["environments"]) == 2
