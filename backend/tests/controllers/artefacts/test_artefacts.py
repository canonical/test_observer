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
from sqlalchemy.orm import Session
from test_observer.data_access.models import Environment, TestExecution

from tests.helpers import create_artefact, create_artefact_builds


def test_get_artefact(db_session: Session, test_client: TestClient):
    artefact = create_artefact(db_session, "beta")
    artefact_build = create_artefact_builds(db_session, artefact, 1)[0]
    environment = Environment(
        name="some-environment", architecture=artefact_build.architecture
    )
    test_execution = TestExecution(
        artefact_build=artefact_build, environment=environment
    )
    db_session.add_all([environment, test_execution])
    db_session.commit()

    response = test_client.get(f"/v1/artefacts/{artefact.id}/builds")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": artefact_build.id,
            "revision": artefact_build.revision,
            "test_executions": [
                {
                    "id": test_execution.id,
                    "jenkins_link": test_execution.jenkins_link,
                    "c3_link": test_execution.c3_link,
                    "environment": {
                        "id": environment.id,
                        "name": environment.name,
                        "architecture": environment.architecture,
                    },
                }
            ],
        }
    ]
