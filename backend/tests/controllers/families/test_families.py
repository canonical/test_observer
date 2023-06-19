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
#        Nadzeya Hutsko <nadzeya.hutsko@canonical.com>


from datetime import datetime, timedelta
from random import randint

from fastapi.testclient import TestClient
from requests_mock import Mocker
from sqlalchemy.orm import Session

from tests.helpers import create_artefact


def test_retreive_family(
    db_session: Session, test_client: TestClient, requests_mock: Mocker
):
    """
    We should get json for a specific family with its stages and artefacts
    """
    # Arrange
    artefact_name_stage_pair = [
        ("core20", "edge", datetime.utcnow()),
        ("oem-jammy", "proposed", datetime.utcnow()),
        ("core20", "edge", datetime.utcnow() - timedelta(days=10)),
        ("core20", "beta", datetime.utcnow() - timedelta(days=20)),
    ]
    artefacts = []
    for name, stage, created_at in artefact_name_stage_pair:
        artefacts.append(
            create_artefact(
                db_session,
                stage,
                name=name,
                created_at=created_at,
                version=str(randint(1, 100)),
            )
        )
    stage = artefacts[0].stage

    # Act
    response = test_client.get("/v1/families/snap")

    # Assert
    assert response.json() == {
        "id": stage.family_id,
        "name": stage.family.name,
        "stages": [
            {
                "id": 1,
                "name": "edge",
                "artefacts": [
                    {
                        "id": artefacts[0].id,
                        "name": artefacts[0].name,
                        "version": artefacts[0].version,
                        "source": artefacts[0].source,
                    }
                ],
            },
            {
                "id": 2,
                "name": "beta",
                "artefacts": [
                    {
                        "id": artefacts[-1].id,
                        "name": artefacts[-1].name,
                        "version": artefacts[-1].version,
                        "source": artefacts[-1].source,
                    }
                ],
            },
            {"id": 3, "name": "candidate", "artefacts": []},
            {"id": 4, "name": "stable", "artefacts": []},
        ],
    }
