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
from operator import itemgetter
from typing import Any, TypeAlias

import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from httpx import Response

from test_observer.data_access.models import TestExecution
from test_observer.data_access.models_enums import StageName
from tests.data_generator import DataGenerator

reruns_url = "/v1/test-executions/reruns"


@pytest.fixture
def post(test_client: TestClient):
    def post_helper(data: Any) -> Response:  # noqa: ANN401
        return test_client.post(reruns_url, json=data)

    return post_helper


@pytest.fixture
def get(test_client: TestClient):
    def get_helper() -> Response:
        return test_client.get(reruns_url)

    return get_helper


@pytest.fixture
def delete(test_client: TestClient):
    def delete_helper(data: Any) -> Response:  # noqa: ANN401
        return test_client.request("DELETE", reruns_url, json=data)

    return delete_helper


Post: TypeAlias = Callable[[Any], Response]
Get: TypeAlias = Callable[[], Response]
Delete: TypeAlias = Callable[[Any], Response]


def test_execution_to_pending_rerun(test_execution: TestExecution) -> dict:
    return jsonable_encoder(
        {
            "test_execution_id": test_execution.id,
            "ci_link": test_execution.ci_link,
            "family": test_execution.artefact_build.artefact.family,
            "test_execution": {
                "id": test_execution.id,
                "ci_link": test_execution.ci_link,
                "c3_link": test_execution.c3_link,
                "environment": {
                    "id": test_execution.environment.id,
                    "name": test_execution.environment.name,
                    "architecture": test_execution.environment.architecture,
                },
                "status": test_execution.status,
                "test_plan": test_execution.test_plan,
                "is_rerun_requested": bool(test_execution.rerun_request),
                "created_at": test_execution.created_at.isoformat(),
            },
            "artefact": {
                "id": test_execution.artefact_build.artefact.id,
                "name": test_execution.artefact_build.artefact.name,
                "version": test_execution.artefact_build.artefact.version,
                "track": test_execution.artefact_build.artefact.track,
                "store": test_execution.artefact_build.artefact.store,
                "series": test_execution.artefact_build.artefact.series,
                "repo": test_execution.artefact_build.artefact.repo,
                "os": test_execution.artefact_build.artefact.os,
                "release": test_execution.artefact_build.artefact.release,
                "sha256": test_execution.artefact_build.artefact.sha256,
                "image_url": test_execution.artefact_build.artefact.image_url,
                "owner": test_execution.artefact_build.artefact.owner,
                "stage": test_execution.artefact_build.artefact.stage,
                "status": test_execution.artefact_build.artefact.status,
                "assignee": test_execution.artefact_build.artefact.assignee,
                "due_date": test_execution.artefact_build.artefact.due_date,
                "bug_link": test_execution.artefact_build.artefact.bug_link,
                "all_environment_reviews_count": (
                    test_execution.artefact_build.artefact.all_environment_reviews_count
                ),
                "completed_environment_reviews_count": (
                    test_execution.artefact_build.artefact.completed_environment_reviews_count
                ),
                "family": test_execution.artefact_build.artefact.family,
                "created_at": test_execution.artefact_build.artefact.created_at.isoformat(),
            },
            "artefact_build": {
                "id": test_execution.artefact_build.id,
                "architecture": test_execution.artefact_build.architecture,
                "revision": test_execution.artefact_build.revision,
            },
        }
    )


def test_post_no_data_returns_422(post: Post):
    assert post(None).status_code == 422


def test_post_invalid_id_returns_404_with_message(post: Post):
    response = post({"test_execution_ids": [1]})
    assert response.status_code == 404
    assert response.json()["detail"] == "Didn't find test executions with provided ids"


def test_valid_post(post: Post, test_execution: TestExecution):
    test_execution.ci_link = "ci.link"
    response = post({"test_execution_ids": [test_execution.id]})

    assert response.status_code == 200
    assert response.json() == [test_execution_to_pending_rerun(test_execution)]


def test_post_with_valid_and_invalid_ids(post: Post, test_execution: TestExecution):
    test_execution.ci_link = "ci.link"
    response = post({"test_execution_ids": [test_execution.id, test_execution.id + 1]})
    assert response.status_code == 207


def test_get_returns_200_with_empty_list(get: Get):
    response = get()
    assert response.status_code == 200
    assert response.json() == []


def test_get_after_one_post(get: Get, post: Post, test_execution: TestExecution):
    test_execution.ci_link = "ci.link"

    post({"test_execution_ids": [test_execution.id]})

    assert get().json() == [test_execution_to_pending_rerun(test_execution)]


def test_get_after_two_identical_posts(
    get: Get, post: Post, test_execution: TestExecution
):
    test_execution.ci_link = "ci.link"

    post({"test_execution_ids": [test_execution.id]})
    post({"test_execution_ids": [test_execution.id]})

    assert get().json() == [test_execution_to_pending_rerun(test_execution)]


def test_get_after_two_different_posts(
    get: Get, post: Post, test_execution: TestExecution, generator: DataGenerator
):
    te1 = test_execution
    te1.ci_link = "ci1.link"

    e2 = generator.gen_environment("desktop")
    te2 = generator.gen_test_execution(te1.artefact_build, e2, ci_link="ci2.link")

    post({"test_execution_ids": [te1.id]})
    post({"test_execution_ids": [te2.id]})

    assert get().json() == [
        test_execution_to_pending_rerun(te1),
        test_execution_to_pending_rerun(te2),
    ]


def test_get_after_post_with_two_test_execution_ids(
    get: Get, post: Post, generator: DataGenerator
):
    a = generator.gen_artefact(StageName.beta)
    ab = generator.gen_artefact_build(a)
    e1 = generator.gen_environment("e1")
    e2 = generator.gen_environment("e2")
    te1 = generator.gen_test_execution(ab, e1, ci_link="ci1.link")
    te2 = generator.gen_test_execution(ab, e2, ci_link="ci2.link")

    post({"test_execution_ids": [te1.id, te2.id]})

    assert sorted(get().json(), key=itemgetter("test_execution_id")) == [
        test_execution_to_pending_rerun(te1),
        test_execution_to_pending_rerun(te2),
    ]


def test_post_delete_get(
    get: Get, post: Post, delete: Delete, test_execution: TestExecution
):
    test_execution.ci_link = "ci.link"
    post({"test_execution_ids": [test_execution.id]})
    response = delete({"test_execution_ids": [test_execution.id]})

    assert response.status_code == 200
    assert get().json() == []
