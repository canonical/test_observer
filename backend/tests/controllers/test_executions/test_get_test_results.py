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


# ruff: noqa: F841 unused defined variables

from fastapi.testclient import TestClient

from test_observer.common.constants import PREVIOUS_TEST_RESULT_COUNT
from test_observer.data_access.models_enums import StageName
from tests.data_generator import DataGenerator


def test_fetch_test_results(test_client: TestClient, generator: DataGenerator):
    environment = generator.gen_environment()
    test_case = generator.gen_test_case(template_id="template")

    artefact_first = generator.gen_artefact(StageName.beta, version="1.1.1")
    artefact_build_first = generator.gen_artefact_build(artefact_first)
    test_execution_first = generator.gen_test_execution(
        artefact_build_first,
        environment,
        ci_link="http://cilink1",
    )
    test_result_first = generator.gen_test_result(
        test_case,
        test_execution_first,
    )

    artefact_second = generator.gen_artefact(StageName.beta, version="1.1.2")
    artefact_build_second = generator.gen_artefact_build(artefact_second)
    test_execution_second = generator.gen_test_execution(
        artefact_build_second,
        environment,
        ci_link="http://cilink2",
    )
    test_result_second = generator.gen_test_result(
        test_case,
        test_execution_second,
    )

    issue = generator.gen_issue()
    response = test_client.post(
        f"/v1/issues/{issue.id}/attach", json={"test_results": [test_result_second.id]}
    )

    response = test_client.get(
        f"/v1/test-executions/{test_execution_second.id}/test-results"
    )

    assert response.status_code == 200
    json = response.json()
    assert json[0]["name"] == test_case.name
    assert json[0]["category"] == test_case.category
    assert json[0]["template_id"] == test_case.template_id
    assert json[0]["status"] == test_result_second.status.name
    assert json[0]["comment"] == test_result_second.comment
    assert json[0]["io_log"] == test_result_second.io_log
    assert json[0]["previous_results"] == [
        {
            "status": test_result_first.status,
            "version": artefact_first.version,
            "artefact_id": artefact_first.id,
        }
    ]
    assert json[0]["issues"] == [
        {
            "issue": {
                "id": issue.id,
                "source": issue.source,
                "project": issue.project,
                "key": issue.key,
                "title": issue.title,
                "status": issue.status,
                "url": issue.url,
            }
        }
    ]


def test_previous_results_shows_reruns(
    test_client: TestClient, generator: DataGenerator
):
    e = generator.gen_environment()
    tc = generator.gen_test_case()

    a = generator.gen_artefact(StageName.beta, version="1")
    ab = generator.gen_artefact_build(a)

    te1 = generator.gen_test_execution(ab, e)
    te2 = generator.gen_test_execution(ab, e)

    tr1 = generator.gen_test_result(tc, te1)
    tr2 = generator.gen_test_result(tc, te2)

    response = test_client.get(f"/v1/test-executions/{te2.id}/test-results")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": tr2.id,
            "name": tc.name,
            "category": tc.category,
            "template_id": tc.template_id,
            "status": tr2.status.name,
            "comment": tr2.comment,
            "io_log": tr2.io_log,
            "previous_results": [
                {
                    "status": tr1.status,
                    "version": a.version,
                    "artefact_id": a.id,
                }
            ],
            "issues": [],
        }
    ]


def test_previous_results_orders_by_artefact(
    test_client: TestClient, generator: DataGenerator
):
    e = generator.gen_environment()
    tc = generator.gen_test_case()

    a1 = generator.gen_artefact(StageName.candidate, version="1")
    a2 = generator.gen_artefact(StageName.beta, version="2")

    ab1 = generator.gen_artefact_build(a1)
    ab2 = generator.gen_artefact_build(a2)

    te2 = generator.gen_test_execution(ab2, e)
    te1 = generator.gen_test_execution(ab1, e)

    tr2 = generator.gen_test_result(tc, te2)
    tr1 = generator.gen_test_result(tc, te1)

    response = test_client.get(f"/v1/test-executions/{te2.id}/test-results")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": tr2.id,
            "name": tc.name,
            "category": tc.category,
            "template_id": tc.template_id,
            "status": tr2.status.name,
            "comment": tr2.comment,
            "io_log": tr2.io_log,
            "previous_results": [
                {
                    "status": tr1.status,
                    "version": a1.version,
                    "artefact_id": a1.id,
                }
            ],
            "issues": [],
        }
    ]


def test_shows_up_to_maximum_previous_results(
    test_client: TestClient, generator: DataGenerator
):
    e = generator.gen_environment()
    tc = generator.gen_test_case()

    a = generator.gen_artefact(StageName.beta, version="1")
    ab = generator.gen_artefact_build(a)

    for _ in range(PREVIOUS_TEST_RESULT_COUNT * 2):
        te = generator.gen_test_execution(ab, e)
        generator.gen_test_result(tc, te)

    response = test_client.get(f"/v1/test-executions/{te.id}/test-results")

    assert response.status_code == 200
    assert len(response.json()[0]["previous_results"]) == PREVIOUS_TEST_RESULT_COUNT
