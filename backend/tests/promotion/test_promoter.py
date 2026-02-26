# Copyright 2024 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Test promoter API"""

from datetime import datetime, timedelta

from requests_mock import Mocker
from sqlalchemy.orm import Session

from test_observer.data_access.models import ArtefactBuild
from test_observer.data_access.models_enums import FamilyName, StageName
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
        StageName.edge,
        family=FamilyName.snap,
        name="core20",
        version="1.1.1",
        store="ubuntu",
        created_at=datetime.utcnow(),
    )
    build = generator.gen_artefact_build(artefact, revision=1)

    requests_mock.get(
        "https://api.snapcraft.io/v2/snaps/info/core20",
        json={
            "channel-map": [
                {
                    "channel": {
                        "architecture": build.architecture,
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
                    "revision": build.revision,
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
    assert artefact.stage == StageName.beta


def test_archives_snap_if_not_found(
    generator: DataGenerator,
    db_session: Session,
    requests_mock: Mocker,
):
    a = generator.gen_artefact(
        family=FamilyName.snap,
        stage=StageName.edge,
        name="core20",
        version="1.1.1",
        store="ubuntu",
    )
    generator.gen_artefact_build(a)

    requests_mock.get(
        f"https://api.snapcraft.io/v2/snaps/info/{a.name}",
        json={"channel-map": []},
    )

    promote_artefacts(db_session)

    assert a.archived


def test_custom_named_snaps_not_archived(
    generator: DataGenerator,
    db_session: Session,
    requests_mock: Mocker,
):
    a = generator.gen_artefact(
        family=FamilyName.snap,
        stage=StageName.edge,
        name="mycore20",
        version="1.1.1",
        store="ubuntu",
    )
    generator.gen_artefact_build(a)

    requests_mock.get(f"https://api.snapcraft.io/v2/snaps/info/{a.name}", status_code=404)

    promote_artefacts(db_session)

    assert not a.archived


def test_promote_snap_from_beta_to_stable(
    db_session: Session,
    requests_mock: Mocker,
    generator: DataGenerator,
):
    artefact = generator.gen_artefact(StageName.beta, store="ubuntu")
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

    assert artefact.stage == StageName.stable


def test_snap_that_is_in_two_stages(
    db_session: Session,
    requests_mock: Mocker,
    generator: DataGenerator,
):
    artefact = generator.gen_artefact(StageName.edge, store="ubuntu")
    build = generator.gen_artefact_build(artefact, revision=1)

    requests_mock.get(
        f"https://api.snapcraft.io/v2/snaps/info/{artefact.name}",
        json={
            "channel-map": [
                {
                    "channel": {
                        "architecture": build.architecture,
                        "risk": "beta",
                        "track": artefact.track,
                    },
                    "revision": build.revision,
                    "type": "app",
                    "version": artefact.version,
                },
                {
                    "channel": {
                        "architecture": build.architecture,
                        "risk": "edge",
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

    assert artefact.stage == StageName.beta


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
        StageName.proposed,
        family=FamilyName.deb,
        name="linux-generic",
        version="5.19.0.43.39",
        series="kinetic",
        repo="main",
        created_at=datetime.utcnow(),
    )
    artefact2 = generator.gen_artefact(
        StageName.proposed,
        family=FamilyName.deb,
        name="linux-oem-22_04a",
        version="6.1.0.1028.29",
        series="kinetic",
        repo="main",
        created_at=datetime.utcnow() - timedelta(days=1),
    )
    artefact3 = generator.gen_artefact(
        StageName.proposed,
        family=FamilyName.deb,
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

    _prepare_archive_mock(requests_mock)

    # Act
    promote_artefacts(db_session)

    db_session.refresh(artefact1)

    # Assert
    assert artefact1.stage == StageName.updates
    assert artefact2.stage == StageName.updates
    assert artefact3.stage == StageName.updates


def test_archives_deb_if_version_not_found(generator: DataGenerator, db_session: Session, requests_mock: Mocker):
    a = generator.gen_artefact(
        family=FamilyName.deb,
        stage=StageName.updates,
        name="linux-generic",
        version="missing-version",
        series="kinetic",
        repo="main",
    )
    generator.gen_artefact_build(a, "amd64")

    _prepare_archive_mock(requests_mock)

    promote_artefacts(db_session)

    assert a.archived


def test_keeps_deb_unarchived_if_custom_name(generator: DataGenerator, db_session: Session, requests_mock: Mocker):
    a = generator.gen_artefact(
        family=FamilyName.deb,
        stage=StageName.updates,
        name="some-custom-name",
        version="5.15.0-86.96",
        series="kinetic",
        repo="main",
    )
    generator.gen_artefact_build(a, "amd64")

    _prepare_archive_mock(requests_mock)

    promote_artefacts(db_session)

    assert not a.archived


def _prepare_archive_mock(requests_mock: Mocker) -> None:
    with open("tests/test_data/Packages-proposed.gz", "rb") as f:
        proposed_content = f.read()
    with open("tests/test_data/Packages-updates.gz", "rb") as f:
        updates_content = f.read()

    requests_mock.get(
        "http://us.archive.ubuntu.com/ubuntu/dists/kinetic-proposed/main/binary-amd64/Packages.gz",
        content=proposed_content,
    )
    requests_mock.get(
        "http://us.archive.ubuntu.com/ubuntu/dists/kinetic-updates/main/binary-amd64/Packages.gz",
        content=updates_content,
    )
