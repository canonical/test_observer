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


from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from test_observer.data_access.models_enums import (
    StageName,
    TestExecutionStatus,
    TestResultStatus,
)
from tests.data_generator import DataGenerator


def test_report_test_execution_data(test_client: TestClient, generator: DataGenerator):
    c3_link = "http://c3.localhost"
    artefact = generator.gen_artefact(StageName.beta)
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    initial_relevant_links_for_gen = [
        {"label": "Build Log", "url": "http://example.com/build-log"},
        {"label": "Wiki", "url": "http://example.com/wiki"},
    ]
    test_execution = generator.gen_test_execution(
        artefact_build,
        environment,
        ci_link="http://localhost",
        relevant_links=initial_relevant_links_for_gen,
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
            "relevant_links": [
                {"label": link.label, "url": link.url}
                for link in test_execution.relevant_links
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
    assert len(test_execution.relevant_links) == 2
    assert test_execution.relevant_links[0].label == "Build Log"
    assert test_execution.relevant_links[0].url == "http://example.com/build-log"
    assert test_execution.relevant_links[1].label == "Wiki"
    assert test_execution.relevant_links[1].url == "http://example.com/wiki"


def test_end_test_is_idempotent(
    test_client: TestClient, generator: DataGenerator, db_session: Session
):
    artefact = generator.gen_artefact(StageName.beta)
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build,
        environment,
        ci_link="http://localhost",
        relevant_links=[{"label": "Docs", "url": "http://docs.example.com"}],
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
                "relevant_links": [
                    {"label": link.label, "url": link.url}
                    for link in test_execution.relevant_links
                ],
            },
        )

    db_session.refresh(test_execution)
    assert len(test_execution.test_results) == 1
    assert len(test_execution.relevant_links) == 1
    assert test_execution.relevant_links[0].label == "Docs"
    assert test_execution.relevant_links[0].url == "http://docs.example.com"


def test_end_test_updates_template_id(
    test_client: TestClient, generator: DataGenerator
):
    artefact = generator.gen_artefact(StageName.beta)
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build,
        environment,
        ci_link="http://localhost",
        relevant_links=[{"label": "Report", "url": "http://report.example.com"}],
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
            "relevant_links": [
                {"label": link.label, "url": link.url}
                for link in test_execution.relevant_links
            ],
        },
    )

    assert response.status_code == 200
    assert test_execution.test_results[0].test_case.template_id == "some template id"
    assert len(test_execution.relevant_links) == 1
    assert test_execution.relevant_links[0].label == "Report"
    assert test_execution.relevant_links[0].url == "http://report.example.com"
