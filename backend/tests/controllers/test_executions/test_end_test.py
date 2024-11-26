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

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from test_observer.data_access.models_enums import (
    TestExecutionStatus,
    TestResultStatus,
)
from tests.data_generator import DataGenerator


def test_report_test_execution_data(test_client: TestClient, generator: DataGenerator):
    c3_link = "http://c3.localhost"
    artefact = generator.gen_artefact("beta")
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build, environment, ci_link="http://localhost"
    )
    generator.gen_artefact_build_environment_review(artefact_build, environment)
    test_case = generator.gen_test_case()

    response = test_client.put(
        "/v1/test-executions/end-test",
        json={
            "ci_link": test_execution.ci_link,
            "c3_link": c3_link,
            "checkbox_version": "3.3.0",
            "test_results": [
                {
                    "name": test_case.name,
                    "status": "pass",
                    "category": test_case.category,
                    "comment": "",
                    "io_log": "",
                },
                {
                    "name": "disk/stats_nvme0n1",
                    "template_id": "disk/stats_name",
                    "status": "skip",
                    "category": "",
                    "comment": "",
                    "io_log": "",
                },
            ],
        },
    )

    assert response.status_code == 200
    assert test_execution.status == TestExecutionStatus.PASSED
    assert test_execution.c3_link == c3_link
    assert test_execution.checkbox_version == "3.3.0"
    assert test_execution.test_results[0].test_case.name == test_case.name
    assert test_execution.test_results[0].status == TestResultStatus.PASSED
    assert test_execution.test_results[0].test_case.template_id == test_case.template_id
    assert test_execution.test_results[1].test_case.name == "disk/stats_nvme0n1"
    assert test_execution.test_results[1].status == TestResultStatus.SKIPPED
    assert test_execution.test_results[1].test_case.template_id == "disk/stats_name"


def test_end_test_is_idempotent(
    test_client: TestClient, generator: DataGenerator, db_session: Session
):
    artefact = generator.gen_artefact("beta")
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build, environment, ci_link="http://localhost"
    )
    generator.gen_artefact_build_environment_review(artefact_build, environment)

    for _ in range(2):
        test_client.put(
            "/v1/test-executions/end-test",
            json={
                "ci_link": test_execution.ci_link,
                "test_results": [
                    {
                        "name": "test name",
                        "status": "pass",
                        "category": "test category",
                        "comment": "",
                        "io_log": "",
                    }
                ],
            },
        )

    db_session.refresh(test_execution)
    assert len(test_execution.test_results) == 1


def test_end_test_updates_template_id(
    test_client: TestClient, generator: DataGenerator
):
    artefact = generator.gen_artefact("beta")
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build, environment, ci_link="http://localhost"
    )
    generator.gen_artefact_build_environment_review(artefact_build, environment)
    test_case = generator.gen_test_case(template_id="")

    response = test_client.put(
        "/v1/test-executions/end-test",
        json={
            "ci_link": test_execution.ci_link,
            "c3_link": "",
            "test_results": [
                {
                    "name": test_case.name,
                    "status": "pass",
                    "category": test_case.category,
                    "template_id": "some template id",
                    "comment": "",
                    "io_log": "",
                }
            ],
        },
    )

    assert response.status_code == 200
    assert test_execution.test_results[0].test_case.template_id == "some template id"
