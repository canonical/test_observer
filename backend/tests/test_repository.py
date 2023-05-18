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


import pytest

from src.repository import (
    get_stages_by_family_name,
    get_stage_by_name,
    get_family_by_name,
    get_artefacts_by_family_name,
)


def test_get_stages_by_family_name(db_session, seed_db):
    """The function should select correct stages for the specified family name"""
    # Arrange
    family_name = "snap"
    expected_stage_names = ["edge", "beta"]

    # Act
    stages = get_stages_by_family_name(db_session, family_name)

    # Assert
    assert len(stages) == len(expected_stage_names)
    assert all(stage.name in expected_stage_names for stage in stages)


def test_get_stages_by_family_name_no_such_family(seed_db, db_session):
    """The function should return empty list"""
    # Arrange
    family_name = "fake"

    # Act
    stages = get_stages_by_family_name(db_session, family_name)

    # Assert
    assert stages == []


def test_get_stage_by_name(seed_db, db_session):
    """The function should select the correct stage by its name"""
    # Arrange
    family = get_family_by_name(db_session, "deb")
    stage_name = "proposed"

    # Act
    stage = get_stage_by_name(db_session, stage_name, family)

    # Assert
    assert stage.name == stage_name


def test_get_stage_by_name_no_such_stage(seed_db, db_session):
    """The function should return None"""
    # Arrange
    family = get_family_by_name(db_session, "deb")
    stage_name = "fakestage"

    # Act
    stage = get_stage_by_name(db_session, stage_name, family)

    # Assert
    assert stage is None


def test_get_stage_by_name_no_such_family(seed_db, db_session):
    """The function should return None"""
    # Arrange
    family = get_family_by_name(db_session, "deb")
    stage_name = "fakestage"

    # Act
    stage = get_stage_by_name(db_session, stage_name, family)

    # Assert
    assert stage is None


def test_get_artefacts_by_family_name(seed_db, db_session):
    """We should get a valid list of artefacts"""
    # Arrange
    family_name = "snap"
    expected_artefact_names = ["core20", "core22"]

    # Act
    artefacts = get_artefacts_by_family_name(db_session, family_name)

    # Assert
    assert len(artefacts) == len(expected_artefact_names)
    assert all(artefact.name in expected_artefact_names for artefact in artefacts)


def test_get_artefacts_by_family_name_no_such_family(seed_db, db_session):
    """We should get an empty list when there's no such family"""
    # Arrange
    family_name = "fakename"

    # Act
    artefacts = get_artefacts_by_family_name(db_session, family_name)

    # Assert
    assert artefacts == []
