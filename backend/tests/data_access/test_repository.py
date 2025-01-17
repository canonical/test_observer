# Copyright (C) 2023 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Test services functions"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from test_observer.data_access.models_enums import FamilyName, StageName
from test_observer.data_access.repository import get_artefacts_by_family
from tests.data_generator import DataGenerator


def test_get_artefacts_by_family_latest(db_session: Session, generator: DataGenerator):
    """We should get a only latest artefacts in each stage for the specified family"""
    # Arrange
    artefact_tuple = [
        ("core20", FamilyName.snap, StageName.edge, datetime.utcnow(), "1"),
        ("oem-jammy", FamilyName.deb, StageName.proposed, datetime.utcnow(), "1"),
        (
            "core20",
            FamilyName.snap,
            StageName.edge,
            datetime.utcnow() - timedelta(days=10),
            "2",
        ),
        (
            "core20",
            FamilyName.snap,
            StageName.beta,
            datetime.utcnow() - timedelta(days=20),
            "3",
        ),
    ]
    expected_artefacts = {artefact_tuple[0], artefact_tuple[-1]}

    for name, family, stage, created_at, version in artefact_tuple:
        generator.gen_artefact(
            stage,
            family=family,
            name=name,
            created_at=created_at,
            version=version,
        )

    # Act
    artefacts = get_artefacts_by_family(db_session, FamilyName.snap)

    # Assert
    assert len(artefacts) == len(expected_artefacts)
    assert {
        (
            artefact.name,
            artefact.family,
            artefact.stage,
            artefact.created_at,
            artefact.version,
        )
        for artefact in artefacts
    } == expected_artefacts


def test_get_artefacts_by_family_charm_unique(
    db_session: Session, generator: DataGenerator
):
    """For latest charms, artefacts should be unique on name, track, and version"""
    # Arrange
    specs = [
        ("name-1", "track-1", "version-1"),
        ("name-2", "track-1", "version-1"),
        ("name-1", "track-2", "version-1"),
        ("name-1", "track-1", "version-2"),
    ]
    for name, track, version in specs:
        artefact = generator.gen_artefact(
            StageName.edge,
            family=FamilyName.charm,
            name=name,
            version=version,
            track=track,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        generator.gen_artefact_build(
            artefact,
            "arch-1",
        )

    # Act
    artefacts = get_artefacts_by_family(db_session, FamilyName.charm)

    # Assert
    assert len(artefacts) == 4


def test_get_artefacts_by_family_charm_all_architectures(
    db_session: Session, generator: DataGenerator
):
    """For latest charms, artefacts should return all known architectures"""
    # Arrange
    specs = [
        ("version-3", "arch-1", 0),
        ("version-2", "arch-1", -1),
        ("version-1", "arch-2", -2),
    ]
    for version, arch, day in specs:
        artefact = generator.gen_artefact(
            StageName.edge,
            family=FamilyName.charm,
            name="name",
            version=version,
            track="track",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(days=day),
        )
        generator.gen_artefact_build(
            artefact,
            arch,
        )

    # Act
    artefacts = get_artefacts_by_family(db_session, FamilyName.charm)

    # Assert
    assert len(artefacts) == 2
    assert {artefact.version for artefact in artefacts} == {"version-3", "version-1"}
