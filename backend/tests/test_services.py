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
"""Test services functions"""

from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound

from src.data_access.models import Family, Stage, Artefact
from src.services import get_stages_by_family_name, get_stage_by_name


def seed_db(session: Session):
    """Populate database"""
    # Snap family
    family = Family(name="snap")
    session.add(family)
    # Edge stage
    stage = Stage(name="edge", family=family)
    session.add(stage)
    artefact = Artefact(name="core20", stage=stage, version="1.1.1", source={})
    session.add(artefact)
    stage = Stage(name="beta", family=family)
    session.add(stage)
    artefact = Artefact(name="core22", stage=stage, version="1.1.0", source={})
    session.add(artefact)

    # Deb family
    family = Family(name="deb")
    session.add(family)
    # Edge stage
    stage = Stage(name="proposed", family=family)
    session.add(stage)
    artefact = Artefact(name="jammy", stage=stage, version="2.1.1", source={})
    session.add(artefact)
    stage = Stage(name="updates", family=family)
    session.add(stage)
    artefact = Artefact(name="raspi", stage=stage, version="2.1.0", source={})
    session.add(artefact)
    session.commit()


def test_get_stages_by_family_name(db_session):
    # Arrange
    seed_db(db_session)
    family_name = "snap"
    expected_stage_names = ["edge", "beta"]

    # Act
    stages = get_stages_by_family_name(db_session, family_name)

    # Assert
    assert len(stages) == len(expected_stage_names)
    assert all(stage.name in expected_stage_names for stage in stages)
