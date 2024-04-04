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
# Written by:
#        Omar Selo <omar.selo@canonical.com>
#        Nadzeya Hutsko <nadzeya.hutsko@canonical.com>


from fastapi.testclient import TestClient

from tests.data_generator import DataGenerator


def test_fetch_test_results(test_client: TestClient, generator: DataGenerator):
    environment = generator.gen_environment()
    test_case = generator.gen_test_case()

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
    assert json[0]["status"] == test_result_second.status.name
    assert json[0]["comment"] == test_result_second.comment
    assert json[0]["io_log"] == test_result_second.io_log
    assert json[0]["previous_results"] == [
        {
            "status": test_result_first.status,
            "version": artefact_first.version,
        }
    ]
