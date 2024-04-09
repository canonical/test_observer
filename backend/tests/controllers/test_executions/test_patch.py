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

import pytest
from fastapi.testclient import TestClient

from test_observer.data_access.models import (
    TestExecution,
)
from test_observer.data_access.models_enums import (
    TestExecutionReviewDecision,
    TestExecutionStatus,
)
from tests.data_generator import DataGenerator


@pytest.fixture
def test_execution(generator: DataGenerator) -> TestExecution:
    a = generator.gen_artefact("beta")
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment()
    te = generator.gen_test_execution(ab, e, ci_link="http://cilink")

    return te


def test_updates_test_execution(test_client: TestClient, test_execution: TestExecution):
    new_review_decision = [
        TestExecutionReviewDecision.APPROVED_FAULTY_HARDWARE.name,
        TestExecutionReviewDecision.APPROVED_INCONSISTENT_TEST.name,
    ]
    test_client.patch(
        f"/v1/test-executions/{test_execution.id}",
        json={
            "ci_link": "http://ci_link/",
            "c3_link": "http://c3_link/",
            "status": TestExecutionStatus.PASSED.name,
            "review_decision": new_review_decision,
            "review_comment": "Tests fail because of broken keyboard",
        },
    )
    assert test_execution.ci_link == "http://ci_link/"
    assert test_execution.c3_link == "http://c3_link/"
    assert test_execution.status == TestExecutionStatus.PASSED
    assert set(test_execution.review_decision) == set(new_review_decision)
    assert test_execution.review_comment == "Tests fail because of broken keyboard"


def test_review_test_execution_fails_if_both_failed_and_approved(
    test_client: TestClient, test_execution: TestExecution
):
    response = test_client.patch(
        f"/v1/test-executions/{test_execution.id}",
        json={
            "review_decision": [
                TestExecutionReviewDecision.REJECTED.name,
                TestExecutionReviewDecision.APPROVED_INCONSISTENT_TEST.name,
            ],
        },
    )

    assert response.status_code == 422
