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


from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from test_observer.common.permissions import Permission
from test_observer.data_access.models import (
    TestExecution,
)
from test_observer.data_access.models_enums import TestExecutionStatus, TestResultStatus
from tests.data_generator import DataGenerator
from tests.conftest import make_authenticated_request

type Execute = Callable[[int, dict[str, Any]], Response]
type Get = Callable[[int], Response]


@pytest.fixture
def get(test_client: TestClient) -> Get:
    def get_helper(id: int) -> Response:
        return make_authenticated_request(
            lambda: test_client.get(f"/v1/test-executions/{id}"),
            Permission.view_test,
        )

    return get_helper


@pytest.fixture
def execute(test_client: TestClient) -> Execute:
    def execute_helper(id: int, data: dict[str, Any]) -> Response:
        return make_authenticated_request(
            lambda: test_client.patch(f"/v1/test-executions/{id}", json=data),
            Permission.change_test,
        )

    return execute_helper


@pytest.fixture
def sample_execution_metadata() -> dict:
    return {
        "category1": [
            "value1",
            "value2",
        ],
        "category2": [
            "value1",
        ],
    }


def test_get_test_execution(get: Get, test_execution: TestExecution):
    response = get(test_execution.id)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_execution.id
    assert data["ci_link"] == test_execution.ci_link
    assert data["status"] == test_execution.status.value


def test_get_test_execution_not_found(get: Get):
    response = get(999999)

    assert response.status_code == 404
    assert response.json()["detail"] == "TestExecution not found"


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


def test_add_execution_metadata_add_empty(
    execute: Execute, test_execution: TestExecution
):
    response = execute(test_execution.id, {"execution_metadata": {}})

    assert response.json()["execution_metadata"] == {}


def test_add_execution_metadata_add_some(
    execute: Execute, test_execution: TestExecution, sample_execution_metadata: dict
):
    response = execute(
        test_execution.id, {"execution_metadata": sample_execution_metadata}
    )

    assert response.json()["execution_metadata"] == sample_execution_metadata


def test_add_execution_metadata_add_same_twice(
    execute: Execute, test_execution: TestExecution, sample_execution_metadata: dict
):
    response = execute(
        test_execution.id, {"execution_metadata": sample_execution_metadata}
    )
    response = execute(
        test_execution.id, {"execution_metadata": sample_execution_metadata}
    )

    assert response.json()["execution_metadata"] == sample_execution_metadata


def test_add_execution_metadata_add_different(
    execute: Execute, test_execution: TestExecution, sample_execution_metadata: dict
):
    response = execute(
        test_execution.id, {"execution_metadata": sample_execution_metadata}
    )
    response = execute(
        test_execution.id, {"execution_metadata": {"category3": ["value"]}}
    )

    assert response.json()["execution_metadata"] == {
        **sample_execution_metadata,
        "category3": ["value"],
    }


@pytest.mark.parametrize(
    "success,execution_metadata",
    [
        (True, {"category": ["value"]}),
        (True, {"X" * 200: ["value"]}),
        (True, {"category": ["X" * 200]}),
        (False, {"X" * 201: ["value"]}),
        (False, {"category": ["X" * 201]}),
        (False, {"": ["value"]}),
        (False, {"category": [""]}),
    ],
)
def test_add_execution_metadata_test_length(
    execute: Execute,
    test_execution: TestExecution,
    execution_metadata: dict,
    success: bool,
):
    response = execute(test_execution.id, {"execution_metadata": execution_metadata})

    if success:
        assert response.status_code == 200
    else:
        assert response.status_code == 422
