# Copyright 2023 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from collections.abc import Sequence
from datetime import date, datetime
from typing import Any

from pydantic import (
    AliasPath,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    computed_field,
    field_validator,
    model_validator,
)

from test_observer.controllers.execution_metadata.models import ExecutionMetadata
from test_observer.data_access.models_enums import (
    ArtefactBuildEnvironmentReviewDecision,
    ArtefactStatus,
    StageName,
    TestExecutionStatus,
)


class ReviewerResponse(BaseModel):
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
    reviewers: list[ReviewerResponse]
    due_date: date | None
    created_at: datetime
    bug_link: str
    jira_epic: str | None
    all_environment_reviews_count: int
    completed_environment_reviews_count: int

    @computed_field(
        description=("Backward-compatible assignee field. Populated from the first entry in reviewers when present.")
    )
    def assignee(self) -> ReviewerResponse | None:
        return self.reviewers[0] if self.reviewers else None


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
    relevant_links: list[TestExecutionRelevantLinkResponse] = Field(default_factory=list)
    environment: EnvironmentResponse
    status: TestExecutionStatus
    rerun_request: Any = Field(exclude=True)
    test_plan: str = Field(validation_alias=AliasPath("test_plan", "name"))
    created_at: datetime
    execution_metadata: ExecutionMetadata
    is_triaged: bool

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
    jira_epic: str | None = None
    assignee_id: int | None = Field(
        default=None,
        deprecated=True,
        description=(
            "Legacy field. Mapped to reviewer_ids as a single-element list when "
            "reviewer_ids/reviewer_emails are not provided."
        ),
    )
    assignee_email: str | None = Field(
        default=None,
        deprecated=True,
        description=(
            "Legacy field. Mapped to reviewer_emails as a single-element list "
            "when reviewer_ids/reviewer_emails are not provided."
        ),
    )
    reviewer_ids: list[int] | None = Field(
        default=None,
        description=("Reviewer user IDs. Preferred over legacy assignee_id/assignee_email for setting assignees."),
    )
    reviewer_emails: list[str] | None = Field(
        default=None,
        description=("Reviewer emails. Preferred over legacy assignee_id/assignee_email for setting assignees."),
    )

    @model_validator(mode="before")
    @classmethod
    def map_legacy_assignee_fields(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data

        # Backwards compatibility: map legacy assignee fields to reviewer fields
        # only when reviewer fields are not explicitly provided.
        if "reviewer_ids" not in data and "reviewer_emails" not in data:
            if "assignee_id" in data:
                data["reviewer_ids"] = [data["assignee_id"]] if data["assignee_id"] is not None else None
            if "assignee_email" in data:
                data["reviewer_emails"] = [data["assignee_email"]] if data["assignee_email"] is not None else None

        return data


class ArtefactVersionResponse(BaseModel):
    version: str
    artefact_id: int = Field(validation_alias=AliasPath("id"))


class ArtefactBuildMinimalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    architecture: str
    revision: int | None


class ArtefactSearchResponse(BaseModel):
    artefacts: list[str]
    count: int
    limit: int
    offset: int


class ArtefactHistoryItemResponse(BaseModel):
    artefact_id: int
    name: str
    version: str
    stage: str
    created_at: datetime


class ArtefactHistoryResponse(BaseModel):
    count: int
    items: list[ArtefactHistoryItemResponse]


class EnvironmentReviewReviewerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    launchpad_handle: str | None = None
    email: str
    name: str


class ArtefactBuildEnvironmentReviewResponse(BaseModel):
    id: int
    review_decision: list[ArtefactBuildEnvironmentReviewDecision]
    review_comment: str
    environment: EnvironmentResponse
    artefact_build: ArtefactBuildMinimalResponse
    reviewers: list[ReviewerResponse] = []


class EnvironmentReviewPatch(BaseModel):
    id: int | None = None
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
