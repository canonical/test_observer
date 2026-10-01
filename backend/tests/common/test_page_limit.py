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

import json
import os
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from test_observer.common.config import (
    MAX_EXECUTION_PAGE_LIMIT,
    MAX_LISTING_PAGE_LIMIT,
    MAX_RESULT_PAGE_LIMIT,
    int_from_env,
)
from test_observer.common.enums import Permission
from test_observer.main import app
from tests.conftest import override_permissions

EXECUTION_PATHS = {"/v1/test-executions"}
RESULT_PATHS = {"/v1/test-results"}
LISTING_PATHS = {
    "/v1/artefacts/search",
    "/v1/environments",
    "/v1/issues",
    "/v1/test-cases",
    "/v1/test-executions/reruns",
    "/v1/test-plans",
    "/v1/users",
    "/v1/users/me/notifications",
    "/v1/users/{user_id}/notifications",
}
HISTORY_PATH = "/v1/artefacts/history"


def _limit_maximums(schema: dict) -> dict[str, int | None]:
    """The maximum of every `limit` query parameter, by path."""
    maximums = {}
    for path, operations in schema["paths"].items():
        for operation in operations.values():
            for parameter in operation.get("parameters", []):
                if parameter["name"] == "limit" and parameter["in"] == "query":
                    # An optional limit is published as "integer or null".
                    schemas = parameter["schema"].get("anyOf", [parameter["schema"]])
                    maximums[path] = next((x["maximum"] for x in schemas if "maximum" in x), None)
    return maximums


def _expected_maximums(execution: int, result: int, listing: int) -> dict[str, int]:
    return {
        **dict.fromkeys(EXECUTION_PATHS, execution),
        **dict.fromkeys(RESULT_PATHS, result),
        **dict.fromkeys(LISTING_PATHS, listing),
        HISTORY_PATH: min(500, listing),
    }


def test_reads_the_setting_or_the_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("SOME_LIMIT", raising=False)
    assert int_from_env("SOME_LIMIT", 1000, minimum=50) == 1000
    monkeypatch.setenv("SOME_LIMIT", "50")
    assert int_from_env("SOME_LIMIT", 1000, minimum=50) == 50


@pytest.mark.parametrize("raw", ["49", "0", "-5", "many", ""])
def test_rejects_a_value_below_the_minimum_or_not_an_integer(monkeypatch: pytest.MonkeyPatch, raw: str):
    monkeypatch.setenv("SOME_LIMIT", raw)
    with pytest.raises(ValueError, match="SOME_LIMIT must be an integer of at least 50"):
        int_from_env("SOME_LIMIT", 1000, minimum=50)


def test_each_paginated_endpoint_uses_the_maximum_of_its_kind():
    maximums = _limit_maximums(app.openapi())
    expected = _expected_maximums(MAX_EXECUTION_PAGE_LIMIT, MAX_RESULT_PAGE_LIMIT, MAX_LISTING_PAGE_LIMIT)

    assert {path: maximums[path] for path in expected} == expected
    # Every other `limit` is already capped at or below the minimum of all three.
    others = [maximum for path, maximum in maximums.items() if path not in expected and maximum is not None]
    assert all(maximum <= 50 for maximum in others)


def test_a_page_above_the_maximum_is_rejected(test_client: TestClient):
    with override_permissions(*Permission):
        at_maximum = test_client.get("/v1/test-executions", params={"limit": MAX_EXECUTION_PAGE_LIMIT})
        above_maximum = test_client.get("/v1/test-executions", params={"limit": MAX_EXECUTION_PAGE_LIMIT + 1})

    assert at_maximum.status_code == 200
    assert above_maximum.status_code == 422


def test_the_environment_variables_set_each_maximum():
    # The caps are read when the application is imported, so check them in a
    # fresh interpreter rather than reloading modules here. Distinct values
    # show that each endpoint reads its own setting.
    script = "import json; from test_observer.main import app; print(json.dumps(app.openapi()))"
    completed = subprocess.run(
        [sys.executable, "-c", script],
        env={
            **os.environ,
            "MAX_EXECUTION_PAGE_LIMIT": "100",
            "MAX_RESULT_PAGE_LIMIT": "300",
            "MAX_LISTING_PAGE_LIMIT": "400",
        },
        capture_output=True,
        text=True,
        check=True,
    )
    maximums = _limit_maximums(json.loads(completed.stdout.splitlines()[-1]))
    expected = _expected_maximums(100, 300, 400)

    assert {path: maximums[path] for path in expected} == expected


def test_the_rerun_queue_caps_an_explicit_limit_but_still_returns_everything_without_one(test_client: TestClient):
    with override_permissions(*Permission):
        above_maximum = test_client.get("/v1/test-executions/reruns", params={"limit": MAX_LISTING_PAGE_LIMIT + 1})
        without_limit = test_client.get("/v1/test-executions/reruns")

    assert above_maximum.status_code == 422
    assert without_limit.status_code == 200
