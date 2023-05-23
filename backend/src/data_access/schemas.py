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
#        Omar Abou Selo <omar.selo@canonical.com>
#        Nadzeya Hutsko <nadzeya.hutsko@canonical.com>
"""Data Transfer Object for creating API responses"""


from typing import List
from datetime import datetime
from pydantic import BaseModel


class ArtefactDTO(BaseModel):
    id: int
    name: str
    version: str
    source: dict
    stage_id: int
    artefact_group_id: int | None
    due_date: datetime | None
    status: str | None

    class Config:
        orm_mode = True


class StageDTO(BaseModel):
    id: int
    name: str
    position: int
    family_id: int
    artefacts: List[ArtefactDTO]

    class Config:
        orm_mode = True


class FamilyDTO(BaseModel):
    id: int
    name: str
    stages: List[StageDTO]

    class Config:
        orm_mode = True
