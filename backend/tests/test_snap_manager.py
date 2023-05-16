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
"""Test snap manager API"""


from src.data_access.models import Artefact
from .conftest import engine


SNAP_CONFIG = """
core20:
    arch: amd64
    store: test-store
    checklists:
        Testflinger:
          expected_tests:
          - caracalla-gpa
          - caracalla-media
"""


def test_snap_manager_valid_yaml(test_app):
    """Check the API's response when provided a valid yaml file."""
    # Act
    response = test_app.post("/snapmanager", files={"file": ("test.yaml", SNAP_CONFIG)})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"detail": "Starting snapmanager job"}


def test_snap_manager_invalid_yaml(test_app):
    """Check the API's response when provided an invalid yaml file."""
    # Arrange
    invalid_yaml = """
    core20:
      arch: amd64
        store: test-store
    """

    # Act
    response = test_app.post(
        "/snapmanager", files={"file": ("test.yaml", invalid_yaml)}
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Error while parsing config"}


def test_run_for_different_revisions(test_app, db_session, requests_mock, mocker):
    """
    If revision in snapcraft response is different from the revision in
    card's name, the card should be archived
    """
    # Arrange
    requests_mock.get(
        "https://api.snapcraft.io/v2/snaps/info/core20",
        json={
            "name": "core20",
            "channel-map": [
                {
                    "channel": {
                        "architecture": "amd64",
                        "name": "edge",
                        "risk": "edge",
                        "track": "latest",
                    },
                    "revision": 1883,
                    "version": "1.1.1",
                }
            ],
        },
    )
    core20 = db_session.query(Artefact).filter(Artefact.name == "core20").first()
    original_stage = core20.stage
    core20.source = {"revision": 1823}
    core20.version = "1.1.1"
    core20.is_archived = False
    db_session.commit()
    mocker.patch("src.main.engine", wraps=engine)

    # Act
    response = test_app.post("/snapmanager", files={"file": ("test.yaml", SNAP_CONFIG)})

    # Assert
    assert response.status_code == 200
    assert core20.stage == original_stage  # The artefact should not be moved
    assert core20.is_archived


def test_run_to_move_artefact(db_session, test_app, requests_mock, mocker):
    """
    If card's current list name is different to its list name in
    snapcraft, the card is moved to the next list
    """
    # Arrange
    requests_mock.get(
        "https://api.snapcraft.io/v2/snaps/info/core20",
        json={
            "name": "core20",
            "channel-map": [
                {
                    "channel": {
                        "architecture": "amd64",
                        "name": "beta",
                        "risk": "beta",
                        "track": "latest",
                    },
                    "revision": 1883,
                    "version": "1.1.1",
                }
            ],
        },
    )
    core20 = db_session.query(Artefact).filter(Artefact.name == "core20").first()
    core20.source = {"revision": 1883}
    core20.version = "1.1.1"
    core20.is_archived = False
    db_session.commit()
    mocker.patch("src.main.engine", wraps=engine)

    # Act
    response = test_app.post("/snapmanager", files={"file": ("test.yaml", SNAP_CONFIG)})

    # Assert
    assert response.status_code == 200
    assert core20.stage.name == "beta"
    assert not core20.is_archived  # The artefact should not be archived
