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


from datetime import datetime, timedelta
from random import randint

from sqlalchemy.orm import Session
from test_observer.data_access.models import Family
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.repository import (
    get_artefacts_by_family_name,
    get_stage_by_name,
)

from ..helpers import create_artefact


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
    """We should get a valid list of all artefacts"""
    # Arrange
    artefact_name_stage_pair = {
        ("core20", "edge"),
        ("core22", "beta"),
        ("docker", "candidate"),
    }

    for name, stage in artefact_name_stage_pair:
        create_artefact(db_session, stage, name=name)

    # Act
    artefacts = get_artefacts_by_family_name(
        db_session, FamilyName.SNAP, latest_only=False
    )

    # Assert
    assert len(artefacts) == len(artefact_name_stage_pair)
    assert {
        (artefact.name, artefact.stage.name) for artefact in artefacts
    } == artefact_name_stage_pair


def test_get_artefacts_by_family_name_latest(db_session: Session):
    """We should get a only latest artefacts in each stage for the specified family"""
    # Arrange
    artefact_name_stage_pair = [
        ("core20", "edge", datetime.utcnow()),
        ("oem-jammy", "proposed", datetime.utcnow()),
        ("core20", "edge", datetime.utcnow() - timedelta(days=10)),
        ("core20", "beta", datetime.utcnow() - timedelta(days=20)),
    ]
    expected_artefacts = {artefact_name_stage_pair[0], artefact_name_stage_pair[-1]}

    for name, stage, created_at in artefact_name_stage_pair:
        create_artefact(
            db_session,
            stage,
            name=name,
            created_at=created_at,
            version=str(randint(1, 100)),
        )

    # Act
    artefacts = get_artefacts_by_family_name(db_session, FamilyName.SNAP)

    # Assert
    assert len(artefacts) == len(expected_artefacts)
    assert {
        (artefact.name, artefact.stage.name, artefact.created_at)
        for artefact in artefacts
    } == expected_artefacts
