# Copyright 2025 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import uuid

from fastapi.testclient import TestClient

from test_observer.common.permissions import Permission
from test_observer.data_access.models_enums import FamilyName, TestExecutionStatus
from tests.conftest import make_authenticated_request
from tests.data_generator import DataGenerator


def _uid(prefix: str = "te_search") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class TestSearchTestExecutions:
    def test_endpoint_exists(self, test_client: TestClient):
        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-executions"),
            Permission.view_test,
        )
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "limit" in data
        assert "offset" in data
        assert "test_executions" in data

    def test_test_result_any_returns_executions_with_results(self, test_client: TestClient, generator: DataGenerator):
        artefact = generator.gen_artefact(name=_uid("artefact"))
        build = generator.gen_artefact_build(artefact)
        env = generator.gen_environment()
        tc = generator.gen_test_case(name=_uid("tc"))

        te_with = generator.gen_test_execution(build, env)
        tr = generator.gen_test_result(tc, te_with)

        te_without = generator.gen_test_execution(build, env)

        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-executions?test_result=any"),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        te_ids = {item["test_execution"]["id"] for item in data["test_executions"]}
        tr_ids = {item["test_result"]["id"] for item in data["test_executions"] if item["test_result"]}

        assert te_with.id in te_ids
        assert tr.id in tr_ids
        assert te_without.id not in te_ids

    def test_test_result_none_returns_executions_without_results(
        self, test_client: TestClient, generator: DataGenerator
    ):
        artefact = generator.gen_artefact(name=_uid("artefact"))
        build = generator.gen_artefact_build(artefact)
        env = generator.gen_environment()
        tc = generator.gen_test_case(name=_uid("tc"))

        te_with = generator.gen_test_execution(build, env)
        generator.gen_test_result(tc, te_with)

        te_without = generator.gen_test_execution(build, env)

        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-executions?test_result=none"),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        te_ids = {item["test_execution"]["id"] for item in data["test_executions"]}

        assert te_without.id in te_ids
        assert te_with.id not in te_ids
        # All items should have null test_result
        assert all(item["test_result"] is None for item in data["test_executions"])

    def test_test_result_none_items_have_null_test_result(self, test_client: TestClient, generator: DataGenerator):
        artefact = generator.gen_artefact(name=_uid("artefact"))
        build = generator.gen_artefact_build(artefact)
        env = generator.gen_environment()

        te = generator.gen_test_execution(build, env)

        response = make_authenticated_request(
            lambda: test_client.get(f"/v1/test-executions?test_result=none&artefacts={artefact.name}"),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        matching = [item for item in data["test_executions"] if item["test_execution"]["id"] == te.id]
        assert len(matching) == 1
        assert matching[0]["test_result"] is None

    def test_test_result_specific_id(self, test_client: TestClient, generator: DataGenerator):
        artefact = generator.gen_artefact(name=_uid("artefact"))
        build = generator.gen_artefact_build(artefact)
        env = generator.gen_environment()
        tc = generator.gen_test_case(name=_uid("tc"))

        te = generator.gen_test_execution(build, env)
        tr1 = generator.gen_test_result(tc, te)
        tr2 = generator.gen_test_result(tc, te)

        response = make_authenticated_request(
            lambda: test_client.get(f"/v1/test-executions?test_result={tr1.id}"),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        tr_ids = {item["test_result"]["id"] for item in data["test_executions"] if item["test_result"]}
        assert tr1.id in tr_ids
        assert tr2.id not in tr_ids

    def test_filter_by_family_with_no_result(self, test_client: TestClient, generator: DataGenerator):
        snap_artefact = generator.gen_artefact(family=FamilyName.snap, name=_uid("snap"))
        deb_artefact = generator.gen_artefact(family=FamilyName.deb, name=_uid("deb"))
        env = generator.gen_environment()

        snap_build = generator.gen_artefact_build(snap_artefact)
        deb_build = generator.gen_artefact_build(deb_artefact)

        snap_te = generator.gen_test_execution(snap_build, env)
        deb_te = generator.gen_test_execution(deb_build, env)

        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-executions?test_result=none&families=snap"),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        te_ids = {item["test_execution"]["id"] for item in data["test_executions"]}
        assert snap_te.id in te_ids
        assert deb_te.id not in te_ids

    def test_filter_by_execution_status_with_no_result(self, test_client: TestClient, generator: DataGenerator):
        artefact = generator.gen_artefact(name=_uid("artefact"))
        build = generator.gen_artefact_build(artefact)
        env = generator.gen_environment()

        te_in_progress = generator.gen_test_execution(build, env, status=TestExecutionStatus.IN_PROGRESS)
        te_not_started = generator.gen_test_execution(build, env, status=TestExecutionStatus.NOT_STARTED)

        response = make_authenticated_request(
            lambda: test_client.get(
                f"/v1/test-executions?test_result=none&test_execution_statuses={TestExecutionStatus.IN_PROGRESS.value}"
            ),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        te_ids = {item["test_execution"]["id"] for item in data["test_executions"]}
        assert te_in_progress.id in te_ids
        assert te_not_started.id not in te_ids

    def test_response_includes_artefact_and_build(self, test_client: TestClient, generator: DataGenerator):
        artefact = generator.gen_artefact(name=_uid("artefact"))
        build = generator.gen_artefact_build(artefact)
        env = generator.gen_environment()
        tc = generator.gen_test_case(name=_uid("tc"))

        te = generator.gen_test_execution(build, env)
        generator.gen_test_result(tc, te)

        response = make_authenticated_request(
            lambda: test_client.get(f"/v1/test-executions?test_result=any&artefacts={artefact.name}"),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["test_executions"]) >= 1
        item = next(i for i in data["test_executions"] if i["test_execution"]["id"] == te.id)
        assert item["artefact"]["id"] == artefact.id
        assert item["artefact_build"]["id"] == build.id

    def test_pagination_metadata(self, test_client: TestClient):
        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-executions?limit=10&offset=0"),
            Permission.view_test,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 0
        assert isinstance(data["count"], int)

    def test_no_test_result_filter_defaults_to_any(self, test_client: TestClient, generator: DataGenerator):
        """When test_result param is omitted, behaves like test_result=any."""
        artefact = generator.gen_artefact(name=_uid("artefact"))
        build = generator.gen_artefact_build(artefact)
        env = generator.gen_environment()
        tc = generator.gen_test_case(name=_uid("tc"))

        te = generator.gen_test_execution(build, env)
        tr = generator.gen_test_result(tc, te)

        response = make_authenticated_request(
            lambda: test_client.get(f"/v1/test-executions?artefacts={artefact.name}"),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        tr_ids = {item["test_result"]["id"] for item in data["test_executions"] if item["test_result"]}
        assert tr.id in tr_ids

    def test_filter_by_environment_with_no_result(self, test_client: TestClient, generator: DataGenerator):
        artefact = generator.gen_artefact(name=_uid("artefact"))
        build = generator.gen_artefact_build(artefact)
        env_a = generator.gen_environment(name=_uid("env_a"))
        env_b = generator.gen_environment(name=_uid("env_b"))

        te_a = generator.gen_test_execution(build, env_a)
        te_b = generator.gen_test_execution(build, env_b)

        response = make_authenticated_request(
            lambda: test_client.get(f"/v1/test-executions?test_result=none&environments={env_a.name}"),
            Permission.view_test,
        )

        assert response.status_code == 200
        te_ids = {item["test_execution"]["id"] for item in response.json()["test_executions"]}
        assert te_a.id in te_ids
        assert te_b.id not in te_ids

    def test_filter_by_rerun_requested_with_no_result(self, test_client: TestClient, generator: DataGenerator):
        artefact = generator.gen_artefact(name=_uid("artefact"))
        build = generator.gen_artefact_build(artefact)
        env_a = generator.gen_environment(name=_uid("env_a"))
        env_b = generator.gen_environment(name=_uid("env_b"))

        te_with_rerun = generator.gen_test_execution(build, env_a)
        generator.gen_rerun_request(te_with_rerun)

        te_without_rerun = generator.gen_test_execution(build, env_b)

        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-executions?test_result=none&rerun_is_requested=true"),
            Permission.view_test,
        )

        assert response.status_code == 200
        te_ids = {item["test_execution"]["id"] for item in response.json()["test_executions"]}
        assert te_with_rerun.id in te_ids
        assert te_without_rerun.id not in te_ids

    def test_filter_by_execution_is_latest_with_no_result(self, test_client: TestClient, generator: DataGenerator):
        artefact = generator.gen_artefact(name=_uid("artefact"))
        build = generator.gen_artefact_build(artefact)
        env = generator.gen_environment()

        older_te = generator.gen_test_execution(build, env)
        newer_te = generator.gen_test_execution(build, env)
        assert newer_te.id > older_te.id

        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-executions?test_result=none&execution_is_latest=true"),
            Permission.view_test,
        )

        assert response.status_code == 200
        te_ids = {item["test_execution"]["id"] for item in response.json()["test_executions"]}
        assert newer_te.id in te_ids
        assert older_te.id not in te_ids

    def test_filter_by_artefact_is_archived_with_no_result(self, test_client: TestClient, generator: DataGenerator):
        archived_artefact = generator.gen_artefact(name=_uid("archived"), archived=True)
        active_artefact = generator.gen_artefact(name=_uid("active"), archived=False)
        env = generator.gen_environment()

        te_archived = generator.gen_test_execution(generator.gen_artefact_build(archived_artefact), env)
        te_active = generator.gen_test_execution(generator.gen_artefact_build(active_artefact), env)

        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-executions?test_result=none&artefact_is_archived=true"),
            Permission.view_test,
        )

        assert response.status_code == 200
        te_ids = {item["test_execution"]["id"] for item in response.json()["test_executions"]}
        assert te_archived.id in te_ids
        assert te_active.id not in te_ids

    def test_filter_by_execution_status_with_any_result(self, test_client: TestClient, generator: DataGenerator):
        artefact = generator.gen_artefact(name=_uid("artefact"))
        build = generator.gen_artefact_build(artefact)
        env = generator.gen_environment()
        tc = generator.gen_test_case(name=_uid("tc"))

        te_passed = generator.gen_test_execution(build, env, status=TestExecutionStatus.PASSED)
        generator.gen_test_result(tc, te_passed)
        te_failed = generator.gen_test_execution(build, env, status=TestExecutionStatus.FAILED)
        generator.gen_test_result(tc, te_failed)

        response = make_authenticated_request(
            lambda: test_client.get(
                f"/v1/test-executions?test_result=any&test_execution_statuses={TestExecutionStatus.PASSED.value}"
            ),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        te_ids = {item["test_execution"]["id"] for item in data["test_executions"]}
        assert te_passed.id in te_ids
        assert te_failed.id not in te_ids

    def test_multiple_specific_test_result_ids(self, test_client: TestClient, generator: DataGenerator):
        artefact = generator.gen_artefact(name=_uid("artefact"))
        build = generator.gen_artefact_build(artefact)
        env = generator.gen_environment()
        tc = generator.gen_test_case(name=_uid("tc"))

        te = generator.gen_test_execution(build, env)
        tr1 = generator.gen_test_result(tc, te)
        tr2 = generator.gen_test_result(tc, te)
        tr3 = generator.gen_test_result(tc, te)

        response = make_authenticated_request(
            lambda: test_client.get(f"/v1/test-executions?test_result={tr1.id}&test_result={tr2.id}"),
            Permission.view_test,
        )

        assert response.status_code == 200
        tr_ids = {item["test_result"]["id"] for item in response.json()["test_executions"] if item["test_result"]}
        assert tr1.id in tr_ids
        assert tr2.id in tr_ids
        assert tr3.id not in tr_ids

    def test_count_reflects_total_not_page_size(self, test_client: TestClient, generator: DataGenerator):
        artefact = generator.gen_artefact(name=_uid("artefact"))
        build = generator.gen_artefact_build(artefact)
        env = generator.gen_environment()
        tc = generator.gen_test_case(name=_uid("tc"))
        te = generator.gen_test_execution(build, env)

        for _ in range(5):
            generator.gen_test_result(tc, te)

        response = make_authenticated_request(
            lambda: test_client.get(f"/v1/test-executions?artefacts={artefact.name}&limit=2"),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["test_executions"]) == 2
        assert data["count"] == 5

    def test_invalid_family_returns_422(self, test_client: TestClient):
        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-executions?families=not_a_family"),
            Permission.view_test,
        )
        assert response.status_code == 422

    def test_no_results_for_nonexistent_artefact(self, test_client: TestClient):
        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-executions?artefacts=nonexistent_artefact_xyz_12345"),
            Permission.view_test,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["test_executions"] == []
