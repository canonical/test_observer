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
#        Omar Selo <omar.selo@canonical.com>
"""Test promoter API"""


from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from requests_mock import Mocker
from sqlalchemy.orm import Session
from test_observer.data_access.models import ArtefactBuild

from tests.helpers import create_artefact


def test_run_to_move_artefact_snap(
    db_session: Session, test_client: TestClient, requests_mock: Mocker
):
    """
    If artefact's current stage name is different to its stage name on
    snapcraft, the artefact is moved to the next stage
    """
    # Arrange
    artefact = create_artefact(
        db_session,
        "edge",
        name="core20",
        version="1.1.1",
        source={"store": "ubuntu"},
        created_at=datetime.utcnow(),
    )
    create_artefact(
        db_session,
        "edge",
        name="core20",
        version="1.1.0",
        source={"store": "ubuntu"},
        created_at=datetime.utcnow() - timedelta(days=1),
    )
    db_session.add_all(
        [
            ArtefactBuild(architecture="amd64", artefact=artefact, revision=1),
            ArtefactBuild(architecture="amd64", artefact=artefact, revision=2),
            ArtefactBuild(architecture="arm64", artefact=artefact, revision=1),
        ]
    )
    db_session.commit()

    requests_mock.get(
        "https://api.snapcraft.io/v2/snaps/info/core20",
        json={
            "channel-map": [
                {
                    "channel": {
                        "architecture": artefact.builds[0].architecture,
                        "name": "beta",
                        "released-at": "2023-05-17T12:39:07.471800+00:00",
                        "risk": "beta",
                        "track": "latest",
                    },
                    "created-at": "2023-04-10T09:59:22.309277+00:00",
                    "download": {
                        "deltas": [],
                        "sha3-384": "70f0",
                        "size": 130830336,
                        "url": "https://api.snapcraft.io/api/v1/snaps/download/...",
                    },
                    "revision": artefact.builds[0].revision,
                    "type": "app",
                    "version": "1.1.1",
                },
            ]
        },
    )

    # Act
    test_client.put("/v0/artefacts/promote")

    db_session.refresh(artefact)

    # Assert
    assert artefact.stage.name == "beta"


def test_run_to_move_artefact_deb(
    db_session: Session, test_client: TestClient, requests_mock: Mocker
):
    """
    If artefact's current stage name is different to its stage name on
    deb archive, the artefact is moved to the next stage
    """
    # Arrange
    artefact = create_artefact(
        db_session,
        "proposed",
        name="linux-generic",
        version="5.19.0.43.39",
        source={"series": "kinetic", "repo": "main"},
        created_at=datetime.utcnow(),
    )
    create_artefact(
        db_session,
        "proposed",
        name="linux-generic",
        version="5.19.0.43.38",
        source={"series": "kinetic", "repo": "main"},
        created_at=datetime.utcnow() - timedelta(days=1),
    )
    db_session.add(ArtefactBuild(architecture="amd64", artefact=artefact))
    db_session.commit()

    with open("tests/test_data/Packages-proposed.gz", "rb") as f:
        proposed_content = f.read()
    with open("tests/test_data/Packages-updates.gz", "rb") as f:
        updates_content = f.read()

    for build in artefact.builds:
        requests_mock.get(
            "http://us.archive.ubuntu.com/ubuntu/dists/kinetic-proposed/main/"
            f"binary-{build.architecture}/Packages.gz",
            content=proposed_content,
        )
        requests_mock.get(
            "http://us.archive.ubuntu.com/ubuntu/dists/kinetic-updates/main/"
            f"binary-{build.architecture}/Packages.gz",
            content=updates_content,
        )

    # Act
    test_client.put("/v0/artefacts/promote")

    db_session.refresh(artefact)

    # Assert
    assert artefact.stage.name == "updates"
