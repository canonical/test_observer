# Copyright (C) 2023 Canonical Ltd.
#
# This file is part of Test Observer Backend.
#
# Test Observer Backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# Test Observer Backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


from datetime import date, datetime
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
    StageName,
)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    launchpad_handle: str
    launchpad_email: str
    name: str


class ArtefactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    version: str
    track: str
    store: str
    branch: str
    series: str
    repo: str
    os: str
    release: str
    owner: str
    sha256: str
    image_url: str
    stage: str
    family: str
    status: ArtefactStatus
    comment: str
    archived: bool
    assignee: UserResponse | None
    due_date: date | None
    created_at: datetime
    bug_link: str
    all_environment_reviews_count: int
    completed_environment_reviews_count: int


class EnvironmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    architecture: str


class TestExecutionResponse(BaseModel):
    __test__ = False

    model_config = ConfigDict(from_attributes=True)

    id: int
    ci_link: str | None
    c3_link: str | None
    environment: EnvironmentResponse
    status: TestExecutionStatus
    rerun_request: Any = Field(exclude=True)
    test_plan: str
    created_at: datetime

    @computed_field
    def is_rerun_requested(self) -> bool:
        return bool(self.rerun_request)


class ArtefactBuildResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    architecture: str
    revision: int | None
    test_executions: list[TestExecutionResponse]


class ArtefactPatch(BaseModel):
    status: ArtefactStatus | None = None
    archived: bool | None = None
    stage: StageName | None = None
    comment: str | None = None


class ArtefactVersionResponse(BaseModel):
    version: str
    artefact_id: int = Field(validation_alias=AliasPath("id"))


class ArtefactBuildMinimalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    architecture: str
    revision: int | None


class ArtefactBuildEnvironmentReviewResponse(BaseModel):
    id: int
    review_decision: list[ArtefactBuildEnvironmentReviewDecision]
    review_comment: str
    environment: EnvironmentResponse
    artefact_build: ArtefactBuildMinimalResponse


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
