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
from datetime import date
from typing import Any

from pydantic import AliasPath, BaseModel, ConfigDict, Field, computed_field

from test_observer.data_access.models_enums import (
    ArtefactStatus,
    TestExecutionReviewDecision,
    TestExecutionStatus,
)


class UserDTO(BaseModel):
    id: int
    launchpad_handle: str
    launchpad_email: str
    name: str


class ArtefactDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    version: str
    track: str
    store: str
    series: str
    repo: str
    stage: str = Field(validation_alias=AliasPath("stage", "name"))
    status: ArtefactStatus
    assignee: UserDTO | None
    due_date: date | None
    bug_link: str
    all_test_executions_count: int = 0
    completed_test_executions_count: int = 0


class EnvironmentDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    architecture: str


class TestExecutionDTO(BaseModel):
    __test__ = False

    model_config = ConfigDict(from_attributes=True)

    id: int
    ci_link: str | None
    c3_link: str | None
    environment: EnvironmentDTO
    status: TestExecutionStatus
    # Since in a test execution there might be tests that fail for different
    # reasons, we allow multiple reasons to be picked for the approval
    review_decision: set[TestExecutionReviewDecision]
    review_comment: str
    rerun_request: Any = Field(exclude=True)

    @computed_field
    def is_rerun_requested(self) -> bool:
        return bool(self.rerun_request)


class ArtefactBuildDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    architecture: str
    revision: int | None
    test_executions: list[TestExecutionDTO]


class ArtefactPatch(BaseModel):
    status: ArtefactStatus
