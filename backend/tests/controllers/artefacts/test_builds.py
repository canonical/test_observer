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
from test_observer.common.permissions import Permission
from tests.data_generator import DataGenerator
from tests.conftest import make_authenticated_request


def test_get_artefact_builds(test_client: TestClient, generator: DataGenerator):
    a = generator.gen_artefact(StageName.beta)
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment()
    te = generator.gen_test_execution(ab, e)

    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefacts/{a.id}/builds"),
        Permission.view_artefact,
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": ab.id,
            "revision": ab.revision,
            "architecture": ab.architecture,
            "test_executions": [
                {
                    "id": te.id,
                    "ci_link": te.ci_link,
                    "c3_link": te.c3_link,
                    "relevant_links": te.relevant_links,
                    "status": te.status.value,
                    "environment": {
                        "id": e.id,
                        "name": e.name,
                        "architecture": e.architecture,
                    },
                    "is_rerun_requested": False,
                    "test_plan": te.test_plan.name,
                    "created_at": te.created_at.isoformat(),
                    "execution_metadata": {},
                    "is_triaged": te.is_triaged,
                }
            ],
        }
    ]


def test_get_artefact_builds_sorts_test_executions_by_environment_name(
    test_client: TestClient, generator: DataGenerator
):
    a = generator.gen_artefact(StageName.beta)
    ab = generator.gen_artefact_build(a)
    e2 = generator.gen_environment("e2")
    e1 = generator.gen_environment("e1")
    te2 = generator.gen_test_execution(ab, e2)
    te1 = generator.gen_test_execution(ab, e1)

    assert make_authenticated_request(
        lambda: test_client.get(f"/v1/artefacts/{a.id}/builds"),
        Permission.view_artefact,
    ).json() == [
        {
            "id": ab.id,
            "revision": ab.revision,
            "architecture": ab.architecture,
            "test_executions": [
                {
                    "id": te1.id,
                    "ci_link": te1.ci_link,
                    "c3_link": te1.c3_link,
                    "relevant_links": te1.relevant_links,
                    "status": te1.status.value,
                    "environment": {
                        "id": e1.id,
                        "name": e1.name,
                        "architecture": e1.architecture,
                    },
                    "is_rerun_requested": False,
                    "test_plan": te1.test_plan.name,
                    "created_at": te1.created_at.isoformat(),
                    "execution_metadata": {},
                    "is_triaged": te1.is_triaged,
                },
                {
                    "id": te2.id,
                    "ci_link": te2.ci_link,
                    "c3_link": te2.c3_link,
                    "relevant_links": te2.relevant_links,
                    "status": te2.status.value,
                    "environment": {
                        "id": e2.id,
                        "name": e2.name,
                        "architecture": e2.architecture,
                    },
                    "is_rerun_requested": False,
                    "test_plan": te2.test_plan.name,
                    "created_at": te2.created_at.isoformat(),
                    "execution_metadata": {},
                    "is_triaged": te2.is_triaged,
                },
            ],
        }
    ]


def test_get_artefact_builds_only_latest(
    test_client: TestClient, generator: DataGenerator
):
    artefact = generator.gen_artefact(StageName.beta)
    generator.gen_artefact_build(artefact=artefact, revision=1)
    artefact_build2 = generator.gen_artefact_build(artefact=artefact, revision=2)

    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefacts/{artefact.id}/builds"),
        Permission.view_artefact,
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": artefact_build2.id,
            "revision": artefact_build2.revision,
            "architecture": artefact_build2.architecture,
            "test_executions": [],
        }
    ]


def test_get_artefact_builds_with_rerun_requested(
    test_client: TestClient, generator: DataGenerator
):
    a = generator.gen_artefact(StageName.beta)
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment()
    te = generator.gen_test_execution(ab, e)
    generator.gen_rerun_request(te)

    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/artefacts/{a.id}/builds"),
        Permission.view_artefact,
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": ab.id,
            "revision": ab.revision,
            "architecture": ab.architecture,
            "test_executions": [
                {
                    "id": te.id,
                    "ci_link": te.ci_link,
                    "c3_link": te.c3_link,
                    "relevant_links": te.relevant_links,
                    "status": te.status.value,
                    "environment": {
                        "id": e.id,
                        "name": e.name,
                        "architecture": e.architecture,
                    },
                    "is_rerun_requested": True,
                    "test_plan": te.test_plan.name,
                    "created_at": te.created_at.isoformat(),
                    "execution_metadata": {},
                    "is_triaged": te.is_triaged,
                }
            ],
        }
    ]
