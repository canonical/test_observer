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
#        Omar Selo <omar.selo@canonical.com>
#        Nadzeya Hutsko <nadzeya.hutsko@canonical.com>
from pydantic import AliasPath, BaseModel, ConfigDict, Field

from test_observer.data_access.models_enums import TestExecutionStatus


class ArtefactDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    version: str
    source: dict[str, int | str]
    stage: str = Field(validation_alias=AliasPath("stage", "name"))


class EnvironmentDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    architecture: str


class TestExecutionDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    jenkins_link: str | None
    c3_link: str | None
    environment: EnvironmentDTO
    status: TestExecutionStatus


class ArtefactBuildDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    architecture: str
    revision: int | None
    test_executions: list[TestExecutionDTO]
