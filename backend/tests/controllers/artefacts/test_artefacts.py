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
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from test_observer.data_access.models import (
    ArtefactBuild,
    Environment,
    TestExecution,
    User,
)
from test_observer.data_access.models_enums import (
    ArtefactStatus,
)
from tests.helpers import create_artefact


def test_get_latest_artefacts_by_family(db_session: Session, test_client: TestClient):
    """Should only get latest artefacts and only ones that belong to given family"""
    relevant_artefact = create_artefact(
        db_session,
        "edge",
        version="2",
        status=ArtefactStatus.MARKED_AS_FAILED,
    )

    old_timestamp = relevant_artefact.created_at - timedelta(days=1)
    create_artefact(db_session, "edge", created_at=old_timestamp, version="1")
    create_artefact(db_session, "proposed")

    response = test_client.get("/v1/artefacts", params={"family": "snap"})

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": relevant_artefact.id,
            "name": relevant_artefact.name,
            "version": relevant_artefact.version,
            "track": relevant_artefact.track,
            "store": relevant_artefact.store,
            "series": relevant_artefact.series,
            "repo": relevant_artefact.repo,
            "stage": relevant_artefact.stage.name,
            "status": relevant_artefact.status,
            "assignee": None,
        }
    ]


def test_get_artefact(db_session: Session, test_client: TestClient):
    """Should be able to fetch an existing artefact"""
    artefact = create_artefact(db_session, "edge", status=ArtefactStatus.APPROVED)
    artefact.assignee = User(launchpad_handle="someuser")
    db_session.commit()

    response = test_client.get(f"/v1/artefacts/{artefact.id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": artefact.id,
        "name": artefact.name,
        "version": artefact.version,
        "track": artefact.track,
        "store": artefact.store,
        "series": artefact.series,
        "repo": artefact.repo,
        "stage": artefact.stage.name,
        "status": artefact.status,
        "assignee": {
            "id": artefact.assignee.id,
            "launchpad_handle": "someuser",
        },
    }


def test_get_artefact_builds(db_session: Session, test_client: TestClient):
    artefact = create_artefact(db_session, "beta")
    artefact_build = ArtefactBuild(architecture="amd64", artefact=artefact, revision=1)
    environment = Environment(
        name="some-environment", architecture=artefact_build.architecture
    )
    test_execution = TestExecution(
        artefact_build=artefact_build, environment=environment
    )
    db_session.add_all([environment, test_execution, artefact_build])
    db_session.commit()

    response = test_client.get(f"/v1/artefacts/{artefact.id}/builds")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": artefact_build.id,
            "revision": artefact_build.revision,
            "architecture": artefact_build.architecture,
            "test_executions": [
                {
                    "id": test_execution.id,
                    "ci_link": test_execution.ci_link,
                    "c3_link": test_execution.c3_link,
                    "status": test_execution.status.value,
                    "environment": {
                        "id": environment.id,
                        "name": environment.name,
                        "architecture": environment.architecture,
                    },
                    "review_decision": [],
                    "review_comment": "",
                }
            ],
        }
    ]


def test_get_artefact_builds_only_latest(db_session: Session, test_client: TestClient):
    artefact = create_artefact(db_session, "beta")
    artefact_build1 = ArtefactBuild(
        architecture="amd64", revision="1", artefact=artefact
    )
    artefact_build2 = ArtefactBuild(
        architecture="amd64", revision="2", artefact=artefact
    )
    db_session.add_all([artefact_build1, artefact_build2])
    db_session.commit()

    response = test_client.get(f"/v1/artefacts/{artefact.id}/builds")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": artefact_build2.id,
            "revision": artefact_build2.revision,
            "architecture": artefact_build2.architecture,
            "test_executions": [],
        }
    ]


def test_artefact_signoff(db_session: Session, test_client: TestClient):
    artefact = create_artefact(db_session, "candidate")

    response = test_client.patch(
        f"/v1/artefacts/{artefact.id}",
        json={"status": ArtefactStatus.APPROVED},
    )

    db_session.refresh(artefact)

    assert response.status_code == 200
    assert artefact.status == ArtefactStatus.APPROVED
    assert response.json() == {
        "id": artefact.id,
        "name": artefact.name,
        "version": artefact.version,
        "track": artefact.track,
        "store": artefact.store,
        "series": artefact.series,
        "repo": artefact.repo,
        "stage": artefact.stage.name,
        "status": artefact.status,
        "assignee": None,
    }
