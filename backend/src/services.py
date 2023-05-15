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

from sqlalchemy.orm import joinedload
from .data_access.models import Family, Stage


def get_stages_by_family_name(session, family_name):
    """
    Fetch stages objects related to specific family

    :session: DB session
    :family_name: Name of the family
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


def get_stage_by_name(session, stage_name):
    """
    Get the stage object by its name

    :session: DB session
    :stage_name: Name of the family
    :return: Stage
    """
    stage = session.query(Stage).filter(Stage.name == stage_name).first()
    return stage
