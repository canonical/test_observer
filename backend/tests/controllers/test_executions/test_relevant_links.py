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

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from test_observer.common.permissions import Permission
from test_observer.data_access.models_enums import StageName
from tests.conftest import make_authenticated_request
from tests.data_generator import DataGenerator


def test_post_relevant_link_success(test_client: TestClient, generator: DataGenerator, db_session: Session):
    artefact = generator.gen_artefact(StageName.beta)
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(artefact_build, environment, ci_link="http://test.ci/link")

    link_data = {"label": "Jira Ticket", "url": "https://jira.example.com/TICKET-123"}
    response = make_authenticated_request(
        lambda: test_client.post(
            f"/v1/test-executions/{test_execution.id}/links",
            json=link_data,
        ),
        Permission.change_test,
    )

    assert response.status_code == 200

    db_session.refresh(test_execution)
    assert len(test_execution.relevant_links) == 1
    assert test_execution.relevant_links[0].label == link_data["label"]


def test_post_relevant_link_test_execution_not_found(test_client: TestClient):
    non_existent_id = 99999
    link_data = {"label": "Fake Link", "url": "http://fake.com"}
    response = make_authenticated_request(
        lambda: test_client.post(
            f"/v1/test-executions/{non_existent_id}/links",
            json=link_data,
        ),
        Permission.change_test,
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "TestExecution not found"}


def test_post_relevant_link_invalid_body(test_client: TestClient, generator: DataGenerator):
    artefact = generator.gen_artefact(StageName.beta)
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(artefact_build, environment, ci_link="http://test.ci/link")

    invalid_link_data_no_url = {"label": "Missing URL"}
    response = make_authenticated_request(
        lambda: test_client.post(
            f"/v1/test-executions/{test_execution.id}/links",
            json=invalid_link_data_no_url,
        ),
        Permission.change_test,
    )
    assert response.status_code == 422

    invalid_link_data_no_label = {"url": "http://missing.label"}
    response = make_authenticated_request(
        lambda: test_client.post(
            f"/v1/test-executions/{test_execution.id}/links",
            json=invalid_link_data_no_label,
        ),
        Permission.change_test,
    )
    assert response.status_code == 422


def test_delete_relevant_link_success(test_client: TestClient, generator: DataGenerator, db_session: Session):
    artefact = generator.gen_artefact(StageName.beta)
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(
        artefact_build,
        environment,
        ci_link="http://test.ci/link",
        relevant_links=[
            {"label": "Link A", "url": "http://link.a"},
            {"label": "Link B", "url": "http://link.b"},
        ],
    )
    db_session.refresh(test_execution)

    link_to_delete_id = test_execution.relevant_links[0].id
    original_link_count = len(test_execution.relevant_links)

    response = make_authenticated_request(
        lambda: test_client.delete(f"/v1/test-executions/{test_execution.id}/links/{link_to_delete_id}"),
        Permission.change_test,
    )

    assert response.status_code == 204
    db_session.refresh(test_execution)
    assert len(test_execution.relevant_links) == original_link_count - 1
    assert not any(link.id == link_to_delete_id for link in test_execution.relevant_links)


def test_delete_relevant_link_test_execution_not_found(test_client: TestClient):
    non_existent_id = 99999
    link_id = 1
    response = make_authenticated_request(
        lambda: test_client.delete(f"/v1/test-executions/{non_existent_id}/links/{link_id}"),
        Permission.change_test,
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "TestExecution not found"}
