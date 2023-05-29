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
"""Test snap manager API"""


from fastapi.testclient import TestClient
from requests_mock import Mocker
from sqlalchemy.orm import Session

from ...helpers import create_artefact


def test_run_for_different_revisions(
    test_client: TestClient, db_session: Session, requests_mock: Mocker
):
    """
    If revision in snapcraft response is different from the revision in
    card's name, the card should be archived
    """
    # Arrange
    requests_mock.get(
        "https://api.snapcraft.io/v2/snaps/info/core20",
        json={
            "channel-map": [
                {
                    "channel": {
                        "architecture": "amd64",
                        "name": "edge",
                        "released-at": "2023-05-17T12:39:07.471800+00:00",
                        "risk": "edge",
                        "track": "latest",
                    },
                    "created-at": "2023-04-10T09:59:22.309277+00:00",
                    "download": {
                        "deltas": [],
                        "sha3-384": "70f0",
                        "size": 130830336,
                        "url": "https://api.snapcraft.io/api/v1/snaps/download/...",
                    },
                    "revision": 2856,
                    "type": "app",
                    "version": "1.1.1",
                },
            ]
        },
    )
    artefact = create_artefact(
        db_session,
        "edge",
        name="core20",
        version="1.1.1",
        source={"revision": 1823, "architecture": "amd64", "store": "ubuntu"},
    )

    # Act
    test_client.post("/artefacts/update")

    db_session.refresh(artefact)

    # Assert
    assert artefact.stage.name == "edge"  # The artefact should not be moved
    assert artefact.is_archived


def test_run_to_move_artefact(
    db_session: Session, test_client: TestClient, requests_mock: Mocker
):
    """
    If card's current list name is different to its list name in
    snapcraft, the card is moved to the next list
    """
    # Arrange
    requests_mock.get(
        "https://api.snapcraft.io/v2/snaps/info/core20",
        json={
            "channel-map": [
                {
                    "channel": {
                        "architecture": "amd64",
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
                    "revision": 1883,
                    "type": "app",
                    "version": "1.1.1",
                },
            ]
        },
    )

    artefact = create_artefact(
        db_session,
        "edge",
        name="core20",
        version="1.1.1",
        source={"revision": 1883, "architecture": "amd64", "store": "ubuntu"},
    )

    # Act
    test_client.post("/artefacts/update")

    db_session.refresh(artefact)

    # Assert
    assert artefact.stage.name == "beta"
    assert not artefact.is_archived  # The artefact should not be archived
