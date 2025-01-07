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

from pydantic import (
    AliasPath,
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
)

from test_observer.data_access.models_enums import (
    ArtefactBuildEnvironmentReviewDecision,
    ArtefactStatus,
    TestExecutionStatus,
)


class UserDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    stage: str
    status: ArtefactStatus
    assignee: UserDTO | None
    due_date: date | None
    bug_link: str
    all_environment_reviews_count: int
    completed_environment_reviews_count: int


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
    rerun_request: Any = Field(exclude=True)
    test_plan: str

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


class ArtefactVersionDTO(BaseModel):
    version: str
    artefact_id: int = Field(validation_alias=AliasPath("id"))


class _EnvironmentReviewArtefactBuild(BaseModel):
    id: int
    architecture: str
    revision: int | None


class ArtefactBuildEnvironmentReviewDTO(BaseModel):
    id: int
    review_decision: list[ArtefactBuildEnvironmentReviewDecision]
    review_comment: str
    environment: EnvironmentDTO
    artefact_build: _EnvironmentReviewArtefactBuild


class EnvironmentReviewPatch(BaseModel):
    review_decision: list[ArtefactBuildEnvironmentReviewDecision] | None = None
    review_comment: str | None = None

    @field_validator("review_decision")
    @classmethod
    def validate_review_decision(
        cls: type["EnvironmentReviewPatch"],
        review_decision: set[ArtefactBuildEnvironmentReviewDecision] | None,
    ) -> set[ArtefactBuildEnvironmentReviewDecision] | None:
        if review_decision is None:
            return review_decision

        if len(review_decision) <= 1:
            return review_decision

        if ArtefactBuildEnvironmentReviewDecision.REJECTED in review_decision:
            raise ValueError("Environment review can either be rejected or approved")
        return review_decision
