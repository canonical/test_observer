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
"""Test services functions"""


from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from test_observer.data_access.models import Family
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.repository import (
    get_artefacts_by_family,
    get_stage_by_name,
)
from tests.data_generator import DataGenerator


def test_get_stage_by_name(db_session: Session):
    """The function should select the correct stage by its name"""
    # Arrange
    family = db_session.query(Family).filter(Family.name == FamilyName.DEB).one()
    stage_name = "proposed"

    # Act
    stage = get_stage_by_name(db_session, stage_name, family)

    # Assert
    assert stage and stage.name == stage_name


def test_get_stage_by_name_no_such_stage(db_session: Session):
    """The function should return None"""
    # Arrange
    family = db_session.query(Family).filter(Family.name == FamilyName.DEB).one()
    stage_name = "fakestage"

    # Act
    stage = get_stage_by_name(db_session, stage_name, family)

    # Assert
    assert stage is None


def test_get_artefacts_by_family_name(db_session: Session, generator: DataGenerator):
    """We should get a valid list of all artefacts"""
    # Arrange
    artefact_name_stage_pair = {
        ("core20", "edge"),
        ("core22", "beta"),
        ("docker", "candidate"),
    }

    for name, stage in artefact_name_stage_pair:
        generator.gen_artefact(stage, name=name)

    # Act
    artefacts = get_artefacts_by_family(db_session, FamilyName.SNAP, latest_only=False)

    # Assert
    assert len(artefacts) == len(artefact_name_stage_pair)
    assert {
        (artefact.name, artefact.stage.name) for artefact in artefacts
    } == artefact_name_stage_pair


def test_get_artefacts_by_family_name_latest(
    db_session: Session, generator: DataGenerator
):
    """We should get a only latest artefacts in each stage for the specified family"""
    # Arrange
    artefact_tuple = [
        ("core20", "snap", "edge", datetime.utcnow(), "1"),
        ("oem-jammy", "deb", "proposed", datetime.utcnow(), "1"),
        ("core20", "snap", "edge", datetime.utcnow() - timedelta(days=10), "2"),
        ("core20", "snap", "beta", datetime.utcnow() - timedelta(days=20), "3"),
    ]
    expected_artefacts = {artefact_tuple[0], artefact_tuple[-1]}

    for name, family, stage, created_at, version in artefact_tuple:
        generator.gen_artefact(
            stage,
            family_name=family,
            name=name,
            created_at=created_at,
            version=version,
        )

    # Act
    artefacts = get_artefacts_by_family(db_session, FamilyName.SNAP)

    # Assert
    assert len(artefacts) == len(expected_artefacts)
    assert {
        (
            artefact.name,
            artefact.stage.family.name,
            artefact.stage.name,
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
            "edge",
            family_name="charm",
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
    artefacts = get_artefacts_by_family(db_session, FamilyName.CHARM)

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
            "edge",
            family_name="charm",
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
    artefacts = get_artefacts_by_family(db_session, FamilyName.CHARM)

    # Assert
    assert len(artefacts) == 2
    assert {artefact.version for artefact in artefacts} == {"version-3", "version-1"}
