# Copyright 2024 Canonical Ltd.
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

from datetime import date, timedelta

from sqlalchemy import event
from sqlalchemy.orm import Mapper, Session
from sqlalchemy.engine.base import Connection

from .models import Artefact, Stage
from .models_enums import FamilyName


@event.listens_for(Artefact, "before_insert")
def receive_before_insert(
    mapper: Mapper, connection: Connection, target: Artefact  # noqa: ARG001
):
    """For non-kernel artefacts, set the defaule due date to now() + 10 days"""
    if target.due_date is not None:
        # Don't overwrite existing due date
        return
    if target.name.startswith("linux-") or target.name.endswith("-kernel"):
        # Snap artefacts can also be kernels, we ignore them
        return
    if target.stage_id is not None:
        session = Session(bind=connection)

        stage = session.get(Stage, target.stage_id)

        if stage and stage.family and stage.family.name != FamilyName.DEB.value:
            target.due_date = date.today() + timedelta(days=10)

        session.close()
