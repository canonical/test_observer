# Copyright 2026 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import uuid

from fastapi.testclient import TestClient

from test_observer.common.enums import Permission
from test_observer.data_access.models_enums import FamilyName
from tests.conftest import make_authenticated_request
from tests.data_generator import DataGenerator


def generate_unique_name(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _seed_test_plans(generator: DataGenerator, count: int, prefix: str = "test_plan") -> list[str]:
    """Helper to create test executions with distinct test plans."""
    art = generator.gen_artefact(name=generate_unique_name("artefact"))
    art_build = generator.gen_artefact_build(art)
    env = generator.gen_environment(name=generate_unique_name("environment"))

    names: list[str] = []
    for i in range(count):
        name = f"{prefix}_{i:03d}_{uuid.uuid4().hex[:6]}"
        generator.gen_test_execution(art_build, env, test_plan=name)
        names.append(name)
    return names


def test_get_test_plans(test_client: TestClient):
    """Test getting test plans endpoint"""
    response = make_authenticated_request(
        lambda: test_client.get("/v1/test-plans"),
        Permission.view_test,
    )

    assert response.status_code == 200
    data = response.json()
    assert "test_plans" in data
    assert isinstance(data["test_plans"], list)


def test_create_test_plan_and_validate_returned(test_client: TestClient, generator: DataGenerator):
    """Test that creates a test plan and validates it is returned in the response"""
    unique_plan_name = f"test_validation_plan_{uuid.uuid4().hex[:8]}"

    artefact = generator.gen_artefact(name=generate_unique_name("plan_validation_artefact"))
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment(name=generate_unique_name("plan_validation_env"))
    generator.gen_test_execution(artefact_build, environment, test_plan=unique_plan_name)

    response = make_authenticated_request(
        lambda: test_client.get("/v1/test-plans"),
        Permission.view_test,
    )

    assert response.status_code == 200
    data = response.json()
    assert unique_plan_name in data["test_plans"]


def test_excludes_test_plans_without_test_executions(test_client: TestClient, generator: DataGenerator):
    """Test plans with no associated test executions should not be returned."""
    orphaned_plan_name = f"orphaned_plan_{uuid.uuid4().hex[:8]}"
    generator.gen_test_plan(name=orphaned_plan_name)

    response = make_authenticated_request(
        lambda: test_client.get("/v1/test-plans"),
        Permission.view_test,
    )

    assert response.status_code == 200
    data = response.json()
    assert orphaned_plan_name not in data["test_plans"]


def test_search_filter_q_ilike(test_client: TestClient, generator: DataGenerator):
    """Search should filter by name (ILIKE)."""
    unique_marker = uuid.uuid4().hex[:8]
    target_name = f"special_search_{unique_marker}"
    other_name = f"other_plan_{unique_marker}"

    art = generator.gen_artefact(name=generate_unique_name("artefact"))
    art_build = generator.gen_artefact_build(art)
    env = generator.gen_environment(name=generate_unique_name("environment"))
    generator.gen_test_execution(art_build, env, test_plan=target_name)
    generator.gen_test_execution(art_build, env, test_plan=other_name)

    resp = make_authenticated_request(
        lambda: test_client.get("/v1/test-plans", params={"q": "special_search"}),
        Permission.view_test,
    )
    assert resp.status_code == 200
    got = resp.json()["test_plans"]
    assert target_name in got
    assert other_name not in got


def test_search_case_insensitive(test_client: TestClient, generator: DataGenerator):
    """Search should be case-insensitive."""
    unique_marker = uuid.uuid4().hex[:8]
    plan_name = f"MixedCase_Plan_{unique_marker}"

    art = generator.gen_artefact(name=generate_unique_name("artefact"))
    art_build = generator.gen_artefact_build(art)
    env = generator.gen_environment(name=generate_unique_name("environment"))
    generator.gen_test_execution(art_build, env, test_plan=plan_name)

    for search_term in ["mixedcase", "MIXEDCASE", "MixedCase"]:
        resp = make_authenticated_request(
            lambda: test_client.get("/v1/test-plans", params={"q": search_term}),  # noqa: B023
            Permission.view_test,
        )
        assert resp.status_code == 200
        assert plan_name in resp.json()["test_plans"]


def test_filter_by_family(test_client: TestClient, generator: DataGenerator):
    """Test plans should be filterable by artefact family."""
    unique_marker = uuid.uuid4().hex[:8]
    snap_plan = f"snap_plan_{unique_marker}"
    charm_plan = f"charm_plan_{unique_marker}"

    env = generator.gen_environment(name=generate_unique_name("environment"))

    snap_artefact = generator.gen_artefact(name=generate_unique_name("snap_artefact"), family=FamilyName.snap)
    snap_build = generator.gen_artefact_build(snap_artefact)
    generator.gen_test_execution(snap_build, env, test_plan=snap_plan)

    charm_artefact = generator.gen_artefact(name=generate_unique_name("charm_artefact"), family=FamilyName.charm)
    charm_build = generator.gen_artefact_build(charm_artefact)
    generator.gen_test_execution(charm_build, env, test_plan=charm_plan)

    resp = make_authenticated_request(
        lambda: test_client.get("/v1/test-plans", params={"families": ["snap"]}),
        Permission.view_test,
    )
    assert resp.status_code == 200
    got = resp.json()["test_plans"]
    assert snap_plan in got
    assert charm_plan not in got


def test_pagination_limits(test_client: TestClient):
    """Test pagination parameter validation"""
    response = make_authenticated_request(
        lambda: test_client.get("/v1/test-plans?limit=1001"),
        Permission.view_test,
    )
    assert response.status_code == 422

    response = make_authenticated_request(
        lambda: test_client.get("/v1/test-plans?offset=-1"),
        Permission.view_test,
    )
    assert response.status_code == 422

    response = make_authenticated_request(
        lambda: test_client.get("/v1/test-plans?limit=0"),
        Permission.view_test,
    )
    assert response.status_code == 422


def test_empty_search_returns_empty_list(test_client: TestClient):
    """Test search with no results returns empty list."""
    resp = make_authenticated_request(
        lambda: test_client.get("/v1/test-plans", params={"q": "nonexistent_plan_xyz_123"}),
        Permission.view_test,
    )
    assert resp.status_code == 200
    assert resp.json()["test_plans"] == []


def test_search_with_pagination(test_client: TestClient, generator: DataGenerator):
    """Search results should respect pagination parameters."""
    unique_marker = uuid.uuid4().hex[:8]
    names = _seed_test_plans(generator, 10, prefix=f"paginated_plan_{unique_marker}")
    expected_sorted = sorted(names)

    resp = make_authenticated_request(
        lambda: test_client.get(
            "/v1/test-plans",
            params={"q": f"paginated_plan_{unique_marker}", "limit": 3, "offset": 0},
        ),
        Permission.view_test,
    )
    assert resp.status_code == 200
    page1 = resp.json()["test_plans"]
    assert page1 == expected_sorted[0:3]

    resp = make_authenticated_request(
        lambda: test_client.get(
            "/v1/test-plans",
            params={"q": f"paginated_plan_{unique_marker}", "limit": 3, "offset": 3},
        ),
        Permission.view_test,
    )
    assert resp.status_code == 200
    page2 = resp.json()["test_plans"]
    assert page2 == expected_sorted[3:6]


def test_get_test_plans_pagination_metadata(test_client: TestClient, generator: DataGenerator):
    """count reflects total results, limit and offset echo back the used values"""
    unique_marker = uuid.uuid4().hex[:8]
    _seed_test_plans(generator, count=5, prefix=f"meta_plan_{unique_marker}")

    resp = make_authenticated_request(
        lambda: test_client.get(
            "/v1/test-plans",
            params={"q": f"meta_plan_{unique_marker}", "limit": 2, "offset": 1},
        ),
        Permission.view_test,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 1
    assert len(data["test_plans"]) == 2
