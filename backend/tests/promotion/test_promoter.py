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

from requests_mock import Mocker
from sqlalchemy.orm import Session

from test_observer.data_access.models import ArtefactBuild
from test_observer.promotion.promoter import promote_artefacts
from tests.data_generator import DataGenerator


def test_run_to_move_artefact_snap(
    db_session: Session,
    requests_mock: Mocker,
    generator: DataGenerator,
):
    """
    If artefact's current stage name is different to its stage name on
    snapcraft, the artefact is moved to the next stage
    """
    # Arrange
    artefact = generator.gen_artefact(
        "edge",
        name="core20",
        version="1.1.1",
        store="ubuntu",
        created_at=datetime.utcnow(),
    )
    generator.gen_artefact(
        "edge",
        name="core20",
        version="1.1.0",
        store="ubuntu",
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
                    "revision": artefact.builds[1].revision,
                    "type": "app",
                    "version": "1.1.1",
                },
            ]
        },
    )

    # Act
    promote_artefacts(db_session)

    db_session.refresh(artefact)

    # Assert
    assert artefact.stage_name == "beta"


def test_run_to_move_artefact_deb(
    db_session: Session,
    requests_mock: Mocker,
    generator: DataGenerator,
):
    """
    If artefact's current stage name is different to its stage name on
    deb archive, the artefact is moved to the next stage
    """
    # Arrange
    artefact1 = generator.gen_artefact(
        "proposed",
        family_name="deb",
        name="linux-generic",
        version="5.19.0.43.39",
        series="kinetic",
        repo="main",
        created_at=datetime.utcnow(),
    )
    artefact2 = generator.gen_artefact(
        "proposed",
        family_name="deb",
        name="linux-oem-22_04a",
        version="6.1.0.1028.29",
        series="kinetic",
        repo="main",
        created_at=datetime.utcnow() - timedelta(days=1),
    )
    artefact3 = generator.gen_artefact(
        "proposed",
        family_name="deb",
        name="linux-cloud-tools-5_15.0-86",
        version="5.15.0-86.96",
        series="kinetic",
        repo="main",
        created_at=datetime.utcnow() - timedelta(days=1),
    )
    db_session.add_all(
        [
            ArtefactBuild(architecture="amd64", artefact=artefact1),
            ArtefactBuild(architecture="amd64", artefact=artefact2),
            ArtefactBuild(architecture="amd64", artefact=artefact3),
        ]
    )
    db_session.commit()

    with open("tests/test_data/Packages-proposed.gz", "rb") as f:
        proposed_content = f.read()
    with open("tests/test_data/Packages-updates.gz", "rb") as f:
        updates_content = f.read()

    requests_mock.get(
        "http://us.archive.ubuntu.com/ubuntu/dists/kinetic-proposed/main/"
        "binary-amd64/Packages.gz",
        content=proposed_content,
    )
    requests_mock.get(
        "http://us.archive.ubuntu.com/ubuntu/dists/kinetic-updates/main/"
        "binary-amd64/Packages.gz",
        content=updates_content,
    )

    # Act
    promote_artefacts(db_session)

    db_session.refresh(artefact1)

    # Assert
    assert artefact1.stage_name == "updates"
    assert artefact2.stage_name == "updates"
    assert artefact3.stage_name == "updates"


def test_promote_snap_from_beta_to_stable(
    db_session: Session,
    requests_mock: Mocker,
    generator: DataGenerator,
):
    artefact = generator.gen_artefact("beta", store="ubuntu")
    build = generator.gen_artefact_build(artefact, revision=1)

    requests_mock.get(
        f"https://api.snapcraft.io/v2/snaps/info/{artefact.name}",
        json={
            "channel-map": [
                {
                    "channel": {
                        "architecture": build.architecture,
                        "risk": "stable",
                        "track": artefact.track,
                    },
                    "revision": build.revision,
                    "type": "app",
                    "version": artefact.version,
                },
            ]
        },
    )

    promote_artefacts(db_session)

    assert artefact.stage_name == "stable"
