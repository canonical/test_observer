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
from types import SimpleNamespace

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


def test_get_artefacts_by_family_charm_latest_architectures(
    db_session: Session, generator: DataGenerator
):
    """For latest charms, latest artefacts should include all unique architectures"""
    # Arrange
    base = SimpleNamespace(
        expect=True,
        name="name-1",
        version="1",
        family="charm",
        track="track-1",
        stage="edge",
        day=0,
        arches=["arch-1"],
    )
    specs = [
        # Base case
        SimpleNamespace(),
        # Family is not Charm
        SimpleNamespace(version="2", family="snap", expect=False),
        # Name different from base (same version)
        SimpleNamespace(name="name-2"),
        # Track different from base (same version)
        SimpleNamespace(track="track-2"),
        # Version different from base (same date, return both)
        SimpleNamespace(version="3"),
        # Stage different from base
        SimpleNamespace(version="4", stage="beta"),
        # Older release than base
        SimpleNamespace(version="5", day=-1, expect=False),
        # Older release than base with unique arch
        SimpleNamespace(version="6", day=-1, arches=["arch-1", "arch-2"]),
    ]

    expected_artefacts = []
    for spec in specs:
        spec = SimpleNamespace(**{**vars(base), **vars(spec)})
        artefact = generator.gen_artefact(
            spec.stage,
            family_name=spec.family,
            name=spec.name,
            version=spec.version,
            track=spec.track,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc)
            + timedelta(days=spec.day),
        )
        for arch in spec.arches:
            generator.gen_artefact_build(
                artefact,
                arch,
            )
        if spec.expect:
            expected_artefacts.append(artefact)

    # Act
    artefacts = get_artefacts_by_family(db_session, FamilyName.CHARM)

    # Assert
    assert sorted([a.id for a in artefacts]) == sorted(
        [a.id for a in expected_artefacts]
    )
