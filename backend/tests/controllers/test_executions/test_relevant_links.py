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

from test_observer.data_access.models_enums import StageName
from tests.data_generator import DataGenerator


def test_post_relevant_link_success(
    test_client: TestClient, 
    generator: DataGenerator, 
    db_session: Session):
    
    artefact = generator.gen_artefact(StageName.beta)
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(artefact_build, environment, ci_link="http://test.ci/link")

    link_data = {"label": "Jira Ticket", "url": "https://jira.example.com/TICKET-123"}
    response = test_client.post(
        f"/v1/test-executions/{test_execution.id}/links",
        json=link_data,
    )

    assert response.status_code == 200

    db_session.refresh(test_execution)
    assert len(test_execution.relevant_links) == 1
    assert test_execution.relevant_links[0].label == link_data["label"]


def test_post_relevant_link_test_execution_not_found(test_client: TestClient):
    non_existent_id = 99999
    link_data = {"label": "Fake Link", "url": "http://fake.com"}
    response = test_client.post(
        f"/v1/test-executions/{non_existent_id}/links",
        json=link_data,
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "TestExecution not found"}


def test_post_relevant_link_invalid_body(
    test_client: TestClient, 
    generator: DataGenerator):

    artefact = generator.gen_artefact(StageName.beta)
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(artefact_build, environment, ci_link="http://test.ci/link")

    invalid_link_data_no_url = {"label": "Missing URL"}
    response = test_client.post(
        f"/v1/test-executions/{test_execution.id}/links",
        json=invalid_link_data_no_url,
    )
    assert response.status_code == 422

    invalid_link_data_no_label = {"url": "http://missing.label"}
    response = test_client.post(
        f"/v1/test-executions/{test_execution.id}/links",
        json=invalid_link_data_no_label,
    )
    assert response.status_code == 422


def test_delete_relevant_link_success(
    test_client: TestClient, 
    generator: DataGenerator, 
    db_session: Session):

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
        ]
    )
    db_session.refresh(test_execution)

    link_to_delete_id = test_execution.relevant_links[0].id
    original_link_count = len(test_execution.relevant_links)

    response = test_client.delete(
        f"/v1/test-executions/{test_execution.id}/links/{link_to_delete_id}"
    )

    assert response.status_code == 204
    db_session.refresh(test_execution)
    assert len(test_execution.relevant_links) == original_link_count - 1
    assert not any(
        link.id == link_to_delete_id for link in test_execution.relevant_links
    )


def test_delete_relevant_link_test_execution_not_found(test_client: TestClient):
    non_existent_id = 99999
    link_id = 1
    response = test_client.delete(
        f"/v1/test-executions/{non_existent_id}/links/{link_id}"
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "TestExecution not found"}
