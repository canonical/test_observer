# Copyright 2023 Canonical Ltd.
# All rights reserved.
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
# ruff: noqa: F841 unused defined variables

from fastapi.testclient import TestClient

from test_observer.data_access.models_enums import TestResultStatus
from tests.data_generator import DataGenerator


def test_fetch_test_results(test_client: TestClient, generator: DataGenerator):
    environment = generator.gen_environment()
    test_case = generator.gen_test_case(template_id="template")

    artefact_first = generator.gen_artefact("beta", version="1.1.1")
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

    artefact_second = generator.gen_artefact("beta", version="1.1.2")
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
            "test_execution_id": test_execution_first.id,
        }
    ]


def test_previous_results_only_uses_latest_builds(
    test_client: TestClient, generator: DataGenerator
):
    e = generator.gen_environment()
    tc = generator.gen_test_case()

    a1 = generator.gen_artefact("beta", version="1")
    a2 = generator.gen_artefact("beta", version="2")

    ab11 = generator.gen_artefact_build(a1, revision=1)
    ab12 = generator.gen_artefact_build(a1, revision=2)
    ab21 = generator.gen_artefact_build(a2, revision=1)
    ab22 = generator.gen_artefact_build(a2, revision=2)

    te11 = generator.gen_test_execution(ab11, e)
    te12 = generator.gen_test_execution(ab12, e)
    te21 = generator.gen_test_execution(ab21, e)
    te22 = generator.gen_test_execution(ab22, e)

    tr11 = generator.gen_test_result(tc, te11, status=TestResultStatus.FAILED)
    tr12 = generator.gen_test_result(tc, te12, status=TestResultStatus.PASSED)
    tr21 = generator.gen_test_result(tc, te21, status=TestResultStatus.FAILED)
    tr22 = generator.gen_test_result(tc, te22, status=TestResultStatus.PASSED)

    response = test_client.get(f"/v1/test-executions/{te22.id}/test-results")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": tr22.id,
            "name": tc.name,
            "category": tc.category,
            "template_id": tc.template_id,
            "status": tr22.status.name,
            "comment": tr22.comment,
            "io_log": tr22.io_log,
            "previous_results": [
                {
                    "status": tr12.status,
                    "version": a1.version,
                    "artefact_id": a1.id,
                    "test_execution_id": te12.id,
                }
            ],
        }
    ]


def test_previous_results_shows_reruns(
    test_client: TestClient, generator: DataGenerator
):
    e = generator.gen_environment()
    tc = generator.gen_test_case()

    a = generator.gen_artefact("beta", version="1")
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
                    "test_execution_id": te1.id,
                }
            ],
        }
    ]
