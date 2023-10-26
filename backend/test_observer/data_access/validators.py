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
"""Functions to validate the whole models (not just specific field)"""

from sqlalchemy import select, event
from sqlalchemy.engine.base import Connection
from sqlalchemy.orm import Mapper

from .models import Stage, Family, Artefact
from .models_enums import FamilyName


@event.listens_for(Artefact, "before_insert")
@event.listens_for(Artefact, "before_update")
def validate_artefact(
    mapper: Mapper, connection: Connection, artefact: Artefact  # noqa: ARG001
) -> None:
    """
    Validate artefact before insertion

    :mapper: the Mapper object. Not used yet but I'm not replacing it with _
             to avoid confusions in future
    :connection: the DB connection
    :artefact: the object to validate
    """
    # Validate source
    stage = select(Stage.family_id).where(Stage.id == artefact.stage_id)
    family_id = connection.execute(stage).scalar()
    stage_family = select(Family.name).where(Family.id == family_id)
    family_name = connection.execute(stage_family).scalar()
    if family_name == FamilyName.SNAP.value:
        # Check that store key is specified
        if "store" not in artefact.source:
            raise ValueError("Snap artefacts should have store key in source")
        # Check that store key has a correct value
        if not isinstance(artefact.source["store"], str):
            raise ValueError("Store key in source field should be a string")
