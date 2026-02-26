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
from tests.data_generator import DataGenerator
from tests.conftest import make_authenticated_request


def generate_unique_name(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def test_get_test_cases(test_client: TestClient):
    """Test getting test cases endpoint"""
    response = make_authenticated_request(
        lambda: test_client.get("/v1/test-cases"),
        Permission.view_test,
    )

    assert response.status_code == 200
    data = response.json()
    assert "test_cases" in data
    assert isinstance(data["test_cases"], list)


def test_get_test_cases_response_format(test_client: TestClient):
    """Test response format"""
    response = make_authenticated_request(
        lambda: test_client.get("/v1/test-cases"),
        Permission.view_test,
    )

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

    response = make_authenticated_request(
        lambda: test_client.get("/v1/test-cases"),
        Permission.view_test,
    )
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

    response = make_authenticated_request(
        lambda: test_client.get("/v1/test-cases"),
        Permission.view_test,
    )
    assert response.status_code == 200

    data = response.json()
    test_cases = data["test_cases"]

    # Verify test case with empty template_id is included
    found_case = any(
        case["test_case"] == test_case.name and case["template_id"] == ""
        for case in test_cases
    )
    assert found_case, f"Test case {test_case.name} with empty template_id not found"


# ---------- New helpers & tests ----------


def _seed_cases(
    generator: DataGenerator,
    count: int,
    prefix: str = "case",
    template_prefix: str = "tpl",
) -> list[str]:
    """
    Seed a number of test cases with results so they appear in the API.
    Creates its own environment and artefact build.
    """
    env = generator.gen_environment()
    art = generator.gen_artefact(name=generate_unique_name("artefact"))
    art_build = generator.gen_artefact_build(art)

    names: list[str] = []
    for i in range(count):
        name = f"{prefix}_{i:03d}_{uuid.uuid4().hex[:6]}"
        tpl = f"{template_prefix}_{i % 3}"
        tc = generator.gen_test_case(name=name, template_id=tpl)
        te = generator.gen_test_execution(art_build, env)
        generator.gen_test_result(tc, te)
        names.append(name)
    return names


def test_default_limit_is_50(test_client: TestClient, generator: DataGenerator):
    """When no limit is passed, endpoint should return up to 50 results."""
    _seed_cases(generator, 60, prefix="default_limit")
    resp = make_authenticated_request(
        lambda: test_client.get("/v1/test-cases"),
        Permission.view_test,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "test_cases" in data
    assert len(data["test_cases"]) <= 50
    assert len(data["test_cases"]) == 50  # exactly 50 when >=50 exist


def test_explicit_limit_and_offset_window(
    test_client: TestClient, generator: DataGenerator
):
    """
    Verify limit/offset produce expected window with deterministic
    ordering by name.
    """
    names = _seed_cases(generator, 20, prefix="window_check")
    # ORDER BY name, template_id; names are unique so sort by name is enough
    expected_sorted = sorted(names)

    resp = make_authenticated_request(
        lambda: test_client.get("/v1/test-cases", params={"limit": 5, "offset": 5}),
        Permission.view_test,
    )
    assert resp.status_code == 200
    got = resp.json()["test_cases"]
    assert len(got) == 5
    got_names = [c["test_case"] for c in got]
    assert got_names == expected_sorted[5:10]


def test_search_filter_q_ilike(test_client: TestClient, generator: DataGenerator):
    """Search should filter by name (ILIKE)."""
    # Create a single shared environment & artefact_build to avoid
    # duplicate environment inserts that can violate unique constraints.
    env = generator.gen_environment()
    art = generator.gen_artefact(name=generate_unique_name("search_art"))
    art_build = generator.gen_artefact_build(art)

    def seed(count: int, prefix: str, tpl_prefix: str) -> list[str]:
        names: list[str] = []
        for i in range(count):
            name = f"{prefix}_{i:03d}_{uuid.uuid4().hex[:6]}"
            tpl = f"{tpl_prefix}_{i % 3}"
            tc = generator.gen_test_case(name=name, template_id=tpl)
            te = generator.gen_test_execution(artefact_build=art_build, environment=env)
            generator.gen_test_result(tc, te)
            names.append(name)
        return names

    seed(5, "cpu_temp", "a")
    seed(5, "disk_io", "b")

    resp = make_authenticated_request(
        lambda: test_client.get("/v1/test-cases", params={"q": "cpu_temp"}),
        Permission.view_test,
    )
    assert resp.status_code == 200
    data = resp.json()["test_cases"]
    assert len(data) > 0
    assert all("cpu_temp" in c["test_case"] for c in data)


def test_limit_validation_rejects_zero(test_client: TestClient):
    """FastAPI should enforce ge=1 on limit and return 422 for limit=0."""
    resp = make_authenticated_request(
        lambda: test_client.get("/v1/test-cases", params={"limit": 0}),
        Permission.view_test,
    )
    assert resp.status_code == 422


def test_ordering_by_name(test_client: TestClient, generator: DataGenerator):
    """Verify that returned items are sorted by name (unique field)."""
    env = generator.gen_environment()
    art = generator.gen_artefact(name=generate_unique_name("ord_art"))
    art_build = generator.gen_artefact_build(art)

    names_tpls = [
        (generate_unique_name("alpha_probe"), "B_tpl"),
        (generate_unique_name("alpha_zoom"), "A_tpl"),
        (generate_unique_name("beta_probe"), "A_tpl"),
        (generate_unique_name("gamma_probe"), "Z_tpl"),
    ]

    for name, tpl in names_tpls:
        tc = generator.gen_test_case(name=name, template_id=tpl)
        te = generator.gen_test_execution(art_build, env)
        generator.gen_test_result(tc, te)

    resp = make_authenticated_request(
        lambda: test_client.get("/v1/test-cases", params={"limit": 50}),
        Permission.view_test,
    )
    assert resp.status_code == 200
    items = resp.json()["test_cases"]

    ours = [i for i in items if any(i["test_case"] == n for n, _ in names_tpls)]
    got_names = [i["test_case"] for i in ours]

    expected_names = sorted([n for n, _ in names_tpls])
    assert got_names == expected_names

    tpl_map = dict(names_tpls)
    assert all(tpl_map[i["test_case"]] == i["template_id"] for i in ours)
