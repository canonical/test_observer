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


from sqlalchemy.orm import Session
from test_observer.data_access.models import Family
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.repository import (
    get_artefacts_by_family_name,
    get_stage_by_name,
    get_latest_builds_for_artefact,
)

from ..helpers import create_artefact, create_artefact_builds


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


def test_get_artefacts_by_family_name(db_session: Session):
    """We should get a valid list of artefacts"""
    # Arrange
    artefact_name_stage_pair = {
        ("core20", "edge"),
        ("core22", "beta"),
        ("docker", "candidate"),
    }

    for name, stage in artefact_name_stage_pair:
        create_artefact(db_session, stage, name=name)

    # Act
    artefacts = get_artefacts_by_family_name(db_session, FamilyName.SNAP)

    # Assert
    assert len(artefacts) == len(artefact_name_stage_pair)
    assert {
        (artefact.name, artefact.stage.name) for artefact in artefacts
    } == artefact_name_stage_pair


def test_get_latest_builds_for_artefact(db_session: Session):
    """
    The function should select the correct latest builds by architecture for a
    given artefact
    """
    # Arrange
    artefact = create_artefact(db_session, stage_name="edge", name="core20")
    create_artefact_builds(db_session, artefact)

    # Act
    latest_builds = get_latest_builds_for_artefact(db_session, artefact)

    # Assert
    # Group returned builds by architecture
    builds_by_arch: dict = {}
    for build in latest_builds:
        if build.architecture not in builds_by_arch:
            builds_by_arch[build.architecture] = []
        builds_by_arch[build.architecture].append(build)

    # Check that for each architecture we have only one build and that it is the latest
    for builds in builds_by_arch.values():
        assert len(builds) == 1
        latest_build = max(builds, key=lambda b: b.created_at)
        assert builds[0] == latest_build


def test_get_latest_builds_for_artefact_no_builds(db_session: Session):
    """The function should return an empty list if no builds exist for the artefact"""
    # Arrange
    # Create an artefact with no builds
    artefact = create_artefact(db_session, stage_name="edge", name="core20")

    # Act
    latest_builds = get_latest_builds_for_artefact(db_session, artefact)

    # Assert
    assert isinstance(latest_builds, list)
    assert len(latest_builds) == 0
