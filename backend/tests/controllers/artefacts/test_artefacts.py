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
from pytest import MonkeyPatch
from sqlalchemy.orm import Session

from test_observer.data_access.models import ArtefactBuild, Environment, TestExecution
from test_observer.data_access.models_enums import TestExecutionStatus
from test_observer.external_apis.c3.c3 import C3Api
from test_observer.external_apis.c3.models import (
    Report,
    SubmissionProcessingStatus,
    SubmissionStatus,
)
from test_observer.main import app
from tests.helpers import create_artefact


def test_get_latest_artefacts_by_family(db_session: Session, test_client: TestClient):
    """Should only get latest artefacts and only ones that belong to given family"""
    relevant_artefact = create_artefact(db_session, "edge", version="2")

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
        }
    ]


def test_get_artefact(db_session: Session, test_client: TestClient):
    """Should be able to fetch an existing artefact"""
    artefact = create_artefact(db_session, "edge")

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
    }


def test_get_artefact_builds(
    db_session: Session, test_client: TestClient, monkeypatch: MonkeyPatch
):
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

    c3api_mock = C3Api("foo", "bar")
    monkeypatch.setattr(c3api_mock, "get_reports", lambda _: {})
    monkeypatch.setattr(c3api_mock, "get_submissions_statuses", lambda _: {})
    app.dependency_overrides[C3Api] = c3api_mock

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
                    "jenkins_link": test_execution.jenkins_link,
                    "c3_link": test_execution.c3_link,
                    "status": TestExecutionStatus.IN_PROGRESS,
                    "environment": {
                        "id": environment.id,
                        "name": environment.name,
                        "architecture": environment.architecture,
                    },
                }
            ],
        }
    ]


def test_get_artefact_builds_only_latest(
    db_session: Session, test_client: TestClient, monkeypatch: MonkeyPatch
):
    artefact = create_artefact(db_session, "beta")
    artefact_build1 = ArtefactBuild(
        architecture="amd64", revision="1", artefact=artefact
    )
    artefact_build2 = ArtefactBuild(
        architecture="amd64", revision="2", artefact=artefact
    )
    db_session.add_all([artefact_build1, artefact_build2])
    db_session.commit()

    c3api_mock = C3Api("foo", "bar")
    monkeypatch.setattr(c3api_mock, "get_reports", lambda _: {})
    monkeypatch.setattr(c3api_mock, "get_submissions_statuses", lambda _: {})
    app.dependency_overrides[C3Api] = c3api_mock

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


def test_correct_test_execution_status(
    db_session: Session, test_client: TestClient, monkeypatch: MonkeyPatch
):
    artefact = create_artefact(db_session, "beta")
    artefact_build = ArtefactBuild(architecture="amd64", artefact=artefact, revision=1)
    environment = Environment(name="laptop", architecture=artefact_build.architecture)
    test_execution = TestExecution(
        artefact_build=artefact_build,
        environment=environment,
        c3_link="https://certification.canonical.com/submissions/status/111111",
    )
    db_session.add_all([artefact_build, environment, test_execution])
    db_session.commit()

    c3api_mock = C3Api("foo", "bar")
    submission_status = SubmissionStatus(
        id=111111,
        status=SubmissionProcessingStatus.PASS,
        report_id=237670,
    )
    monkeypatch.setattr(
        c3api_mock,
        "get_submissions_statuses",
        lambda _: {submission_status.id: submission_status},
    )
    report = Report(id=237670, failed_test_count=0)
    monkeypatch.setattr(c3api_mock, "get_reports", lambda _: {report.id: report})
    app.dependency_overrides[C3Api] = c3api_mock

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
                    "jenkins_link": test_execution.jenkins_link,
                    "c3_link": test_execution.c3_link,
                    "status": TestExecutionStatus.PASSED.value,
                    "environment": {
                        "id": environment.id,
                        "name": environment.name,
                        "architecture": environment.architecture,
                    },
                }
            ],
        }
    ]
