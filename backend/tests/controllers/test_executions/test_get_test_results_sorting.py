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

from test_observer.data_access.models_enums import StageName
from tests.data_generator import DataGenerator


def test_get_test_results_sorts_by_execution_order(
    test_client: TestClient, generator: DataGenerator
):
    a = generator.gen_artefact(StageName.beta)
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment()
    te = generator.gen_test_execution(ab, e)

    tc_deploy = generator.gen_test_case("test_deploy")
    tc_integration = generator.gen_test_case("test_integration")
    tc_teardown = generator.gen_test_case("test_teardown")

    generator.gen_test_result(tc_deploy, te)
    generator.gen_test_result(tc_integration, te)
    generator.gen_test_result(tc_teardown, te)

    response = test_client.get(f"/v1/test-executions/{te.id}/test-results")

    assert response.status_code == 200
    json_response = response.json()

    result_ids = [result["id"] for result in json_response]
    test_names = [result["name"] for result in json_response]

    assert result_ids == sorted(result_ids)

    expected_order = ["test_deploy", "test_integration", "test_teardown"]

    assert test_names == expected_order
