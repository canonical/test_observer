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


from pydantic import BaseModel, HttpUrl
from test_observer.data_access.models_enums import IssueSource, IssueStatus, FamilyName

from pydantic import ConfigDict, Field, AliasPath

from test_observer.controllers.artefacts.models import (
    ArtefactBuildMinimalResponse,
    ArtefactResponse,
    TestExecutionResponse,
)

from test_observer.controllers.test_executions.models import (
    TestResultResponse,
)
from test_observer.controllers.execution_metadata.models import ExecutionMetadata


from .shared_models import (
    MinimalIssueResponse,
    MinimalIssueTestResultAttachmentRuleResponse,
)


class IssueTestResultAttachmentResponse(BaseModel):
    test_result: TestResultResponse = Field(validation_alias=AliasPath("test_result"))
    test_execution: TestExecutionResponse = Field(
        validation_alias=AliasPath("test_result", "test_execution")
    )
    artefact: ArtefactResponse = Field(
        validation_alias=AliasPath(
            "test_result",
            "test_execution",
            "artefact_build",
            "artefact",
        )
    )
    artefact_build: ArtefactBuildMinimalResponse = Field(
        validation_alias=AliasPath("test_result", "test_execution", "artefact_build")
    )


class IssueTestResultAttachmentRulePostRequest(BaseModel):
    enabled: bool = Field(default=True)

    families: list[FamilyName] = Field(default_factory=list)
    environment_names: list[str] = Field(default_factory=list)
    test_case_names: list[str] = Field(default_factory=list)
    template_ids: list[str] = Field(default_factory=list)
    execution_metadata: ExecutionMetadata = Field(default_factory=ExecutionMetadata)


class IssueTestResultAttachmentRulePatchRequest(BaseModel):
    enabled: bool | None = None


class IssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: IssueSource
    project: str
    key: str
    title: str
    status: IssueStatus
    url: HttpUrl

    test_results: list[IssueTestResultAttachmentResponse] = Field(
        validation_alias=AliasPath("test_result_attachments")
    )

    attachment_rules: list[MinimalIssueTestResultAttachmentRuleResponse] = Field(
        validation_alias=AliasPath("test_result_attachment_rules")
    )


class IssuesGetResponse(BaseModel):
    issues: list[MinimalIssueResponse]


class IssuePatchRequest(BaseModel):
    title: str | None = None
    status: IssueStatus | None = None


class IssuePutRequest(IssuePatchRequest):
    url: HttpUrl


class IssueAttachmentRequest(BaseModel):
    test_results: list[int] = Field(default_factory=list)
