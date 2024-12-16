# Copyright 2024 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from collections.abc import Callable
from typing import Any, TypeAlias

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from test_observer.data_access.models import (
    TestExecution,
)
from test_observer.data_access.models_enums import TestExecutionStatus, TestResultStatus
from tests.data_generator import DataGenerator

Execute: TypeAlias = Callable[[int, dict[str, Any]], Response]


@pytest.fixture
def execute(test_client: TestClient) -> Execute:
    def execute_helper(id: int, data: dict[str, Any]) -> Response:
        return test_client.patch(f"/v1/test-executions/{id}", json=data)

    return execute_helper


def test_updates_test_execution(execute: Execute, test_execution: TestExecution):
    execute(
        test_execution.id,
        {
            "ci_link": "http://ci_link/",
            "c3_link": "http://c3_link/",
            "status": "PASSED",
        },
    )
    assert test_execution.ci_link == "http://ci_link/"
    assert test_execution.c3_link == "http://c3_link/"
    assert test_execution.status == TestExecutionStatus.PASSED


def test_set_completed_status_with_failures(
    execute: Execute, test_execution: TestExecution, generator: DataGenerator
):
    c1 = generator.gen_test_case(name="case1")
    c2 = generator.gen_test_case(name="case2")
    generator.gen_test_result(c1, test_execution, status=TestResultStatus.PASSED)
    generator.gen_test_result(c2, test_execution, status=TestResultStatus.FAILED)

    response = execute(test_execution.id, {"status": "COMPLETED"})

    assert response.status_code == 200
    assert response.json()["status"] == "FAILED"
    assert test_execution.status == TestExecutionStatus.FAILED


def test_set_completed_status_all_green(
    execute: Execute, test_execution: TestExecution, generator: DataGenerator
):
    c = generator.gen_test_case()
    generator.gen_test_result(c, test_execution, TestResultStatus.PASSED)

    response = execute(test_execution.id, {"status": "COMPLETED"})

    assert response.status_code == 200
    assert response.json()["status"] == "PASSED"
    assert test_execution.status == TestExecutionStatus.PASSED


def test_set_completed_status_no_results(
    execute: Execute, test_execution: TestExecution
):
    response = execute(test_execution.id, {"status": "COMPLETED"})

    assert response.status_code == 200
    assert response.json()["status"] == "ENDED_PREMATURELY"
    assert test_execution.status == TestExecutionStatus.ENDED_PREMATURELY
