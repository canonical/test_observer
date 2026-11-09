# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the License along with this program.
# If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from test_observer.common.enums import Permission
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuildEnvironmentReview,
)
from tests.conftest import override_permissions
from tests.data_generator import DataGenerator


@pytest.fixture(params=["artefacts", "environment-reviews"])
def audit_source(
    request: pytest.FixtureRequest,
    generator: DataGenerator,
) -> tuple[str, Artefact | ArtefactBuildEnvironmentReview]:
    if request.param == "artefacts":
        source = generator.gen_artefact()
    else:
        artefact = generator.gen_artefact()
        build = generator.gen_artefact_build(artefact)
        environment = generator.gen_environment()
        source = generator.gen_artefact_build_environment_review(build, environment)

    return f"/v1/audit/{request.param}/{source.id}", source


def _update_source(source: Artefact | ArtefactBuildEnvironmentReview) -> None:
    if isinstance(source, Artefact):
        source.comment = "updated"
    else:
        source.review_comment = "updated"


def _permission_for_source(source: Artefact | ArtefactBuildEnvironmentReview) -> Permission:
    if isinstance(source, Artefact):
        return Permission.view_artefact
    return Permission.view_environment_review


def test_list_audit_history(
    test_client: TestClient,
    generator: DataGenerator,
    audit_source: tuple[str, Artefact | ArtefactBuildEnvironmentReview],
):
    endpoint, source = audit_source
    _update_source(source)
    generator.db_session.commit()

    permission = _permission_for_source(source)
    response = test_client.get(endpoint)
    assert response.status_code == 403
    with override_permissions(permission):
        response = test_client.get(endpoint)

    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 2
    assert all(set(entry) == {"id", "created_at", "author"} for entry in entries)
    assert all(
        entry["author"] == {"user_id": None, "application_id": None, "automation_name": "tests"} for entry in entries
    )
    assert [(entry["created_at"], entry["id"]) for entry in entries] == sorted(
        (entry["created_at"], entry["id"]) for entry in entries
    )


def test_audit_detail_returns_typed_metadata_and_source_snapshot(
    test_client: TestClient,
    generator: DataGenerator,
    audit_source: tuple[str, Artefact | ArtefactBuildEnvironmentReview],
):
    endpoint, source = audit_source
    generator.db_session.flush()
    permission = _permission_for_source(source)
    with override_permissions(permission):
        entries = test_client.get(endpoint).json()
        response = test_client.get(f"{endpoint}/{entries[0]['id']}")

    assert response.status_code == 200
    detail = response.json()
    assert set(detail) == {"id", "operation", "created_at", "author", "data"}
    assert detail["id"] == entries[0]["id"]
    assert detail["operation"] == "I"
    assert detail["created_at"] == entries[0]["created_at"]
    assert detail["author"] == entries[0]["author"]
    assert detail["data"]["id"] == source.id
    assert set(detail["data"]) == set(source.__table__.columns.keys())
    assert "audit_pk" not in detail["data"]
    assert "audit_author_id" not in detail["data"]
    if isinstance(source, Artefact):
        assert detail["data"]["comment"] == source.comment
    else:
        assert detail["data"]["review_comment"] == source.review_comment


def test_list_audit_history_is_empty_when_no_audit_exists(
    test_client: TestClient,
    audit_source: tuple[str, Artefact | ArtefactBuildEnvironmentReview],
):
    endpoint, source = audit_source
    missing_endpoint = f"{endpoint.rsplit('/', 1)[0]}/999999999"
    permission = _permission_for_source(source)
    with override_permissions(permission):
        response = test_client.get(missing_endpoint)

    assert response.status_code == 200
    assert response.json() == []


def test_audit_detail_requires_a_matching_parent(
    test_client: TestClient,
    generator: DataGenerator,
    audit_source: tuple[str, Artefact | ArtefactBuildEnvironmentReview],
):
    endpoint, source = audit_source
    generator.db_session.flush()
    if isinstance(source, Artefact):
        other_endpoint = f"/v1/audit/artefacts/{generator.gen_artefact(name='other').id}"
    else:
        other_endpoint = _other_review_endpoint(generator, source)
    permission = _permission_for_source(source)
    with override_permissions(permission):
        audit_id = test_client.get(endpoint).json()[0]["id"]
        mismatched = test_client.get(f"{other_endpoint}/{audit_id}")
        missing = test_client.get(f"{endpoint}/999999999")

    assert mismatched.status_code == 404
    assert missing.status_code == 404


def _other_review_endpoint(
    generator: DataGenerator,
    source: ArtefactBuildEnvironmentReview,
) -> str:
    other_artefact = generator.gen_artefact(name="other")
    other_build = generator.gen_artefact_build(other_artefact)
    other_environment = generator.gen_environment(name="other")
    other_review = generator.gen_artefact_build_environment_review(other_build, other_environment)
    assert other_review.id != source.id
    return f"/v1/audit/environment-reviews/{other_review.id}"


def test_audit_history_remains_readable_after_source_deletion(
    test_client: TestClient,
    generator: DataGenerator,
    db_session: Session,
    audit_source: tuple[str, Artefact | ArtefactBuildEnvironmentReview],
):
    endpoint, source = audit_source
    generator.db_session.flush()
    permission = _permission_for_source(source)
    with override_permissions(permission):
        audit_id = test_client.get(endpoint).json()[0]["id"]

    db_session.delete(source)
    db_session.commit()

    with override_permissions(permission):
        entries = test_client.get(endpoint)
        detail = test_client.get(f"{endpoint}/{audit_id}")
        delete_detail = test_client.get(f"{endpoint}/{entries.json()[-1]['id']}")

    assert entries.status_code == 200
    assert len(entries.json()) == 2
    assert detail.status_code == 200
    assert detail.json()["data"]["id"] == source.id
    assert delete_detail.status_code == 200
    assert delete_detail.json()["operation"] == "D"


def test_list_and_detail_require_the_matching_view_permission(
    test_client: TestClient,
    generator: DataGenerator,
    audit_source: tuple[str, Artefact | ArtefactBuildEnvironmentReview],
):
    endpoint, source = audit_source
    generator.db_session.flush()
    permission = _permission_for_source(source)
    wrong_permission = (
        Permission.view_environment_review if permission == Permission.view_artefact else Permission.view_artefact
    )
    with override_permissions(permission):
        audit_id = test_client.get(endpoint).json()[0]["id"]

    with override_permissions(wrong_permission):
        assert test_client.get(endpoint).status_code == 403
        assert test_client.get(f"{endpoint}/{audit_id}").status_code == 403
