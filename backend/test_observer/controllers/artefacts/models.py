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
from collections.abc import Sequence

from pydantic import (
    AliasPath,
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    HttpUrl,
)

from test_observer.data_access.models_enums import (
    ArtefactBuildEnvironmentReviewDecision,
    ArtefactStatus,
    TestExecutionStatus,
    StageName,
)

from test_observer.controllers.execution_metadata.models import ExecutionMetadata


class AssigneeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    launchpad_handle: str | None = None
    email: str
    launchpad_email: str = Field(
        validation_alias=AliasPath("email"),
        deprecated="launchpad_email is deprecated please use email instead",
    )
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
    source: str
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
    assignee: AssigneeResponse | None
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


class TestExecutionRelevantLinkCreate(BaseModel):
    label: str
    url: HttpUrl


class TestExecutionRelevantLinkResponse(TestExecutionRelevantLinkCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    url: HttpUrl


class TestExecutionResponse(BaseModel):
    __test__ = False

    model_config = ConfigDict(from_attributes=True)

    id: int
    ci_link: str | None
    c3_link: str | None
    relevant_links: list[TestExecutionRelevantLinkResponse] = Field(
        default_factory=list
    )
    environment: EnvironmentResponse
    status: TestExecutionStatus
    rerun_request: Any = Field(exclude=True)
    test_plan: str
    created_at: datetime
    execution_metadata: ExecutionMetadata

    @computed_field
    def is_rerun_requested(self) -> bool:
        return bool(self.rerun_request)

    @field_validator("execution_metadata", mode="before")
    @classmethod
    def collect_execution_metadata(cls, v: Sequence) -> ExecutionMetadata:
        return ExecutionMetadata.from_rows(v)


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
    assignee_id: int | None = None
    assignee_email: str | None = None


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
