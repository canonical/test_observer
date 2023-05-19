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
"""Services for working with objects from DB"""

from sqlalchemy.orm import joinedload, Session
from .data_access.models import Family, Stage, Artefact


def get_stages_by_family_name(session: Session, family_name: str) -> list | None:
    """
    Fetch stages objects related to specific family

    :session: DB session
    :family_name: name of the family
    :return: list of stages
    """
    family = session.query(Family).filter(Family.name == family_name).first()
    if family is None:
        return []
    stages = (
        session.query(Stage)
        .filter(Stage.family_id == family.id)
        .options(joinedload(Stage.artefacts))
        .all()
    )
    return stages


def get_stage_by_name(session: Session, stage_name: str, family: Family) -> Stage:
    """
    Get the stage object by its name

    :session: DB session
    :stage_name: name of the stage
    :family: the Family object where stages are located
    :return: Stage
    """
    stage = (
        session.query(Stage)
        .filter(Stage.name == stage_name, Stage.family == family)
        .first()
    )
    return stage


def get_family_by_name(session: Session, family_name: str):
    """
    Get the family object by its name

    :session: DB session
    :family_name: Name of the family
    :return: Family
    """
    family = session.query(Family).filter(Family.name == family_name).first()
    return family


def get_artefacts_by_family_name(
    session: Session, family_name: str, is_archived: bool = None
):
    """
    Get all the artefacts in a family

    :session: DB session
    :family_name: name of the family
    :is_archived: filter archived/non-archived artefacts. None means "do NOT filter"
    :return: list of Artefacts
    """
    if is_archived is not None:
        artefacts = (
            session.query(Artefact)
            .join(Stage)
            .filter(Stage.family.has(Family.name == family_name))
            .filter(Artefact.is_archived == is_archived)
            .options(joinedload(Artefact.stage))
            .all()
        )
        return artefacts
    artefacts = (
        session.query(Artefact)
        .join(Stage)
        .filter(Stage.family.has(Family.name == family_name))
        .options(joinedload(Artefact.stage))
        .all()
    )
    return artefacts
