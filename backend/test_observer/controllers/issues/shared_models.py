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
from test_observer.data_access.models_enums import IssueSource, IssueStatus

from pydantic import ConfigDict, Field, AliasPath


from pydantic import (
    field_validator,
)

from test_observer.controllers.execution_metadata.models import ExecutionMetadata
from test_observer.data_access.models_enums import (
    FamilyName,
)
from test_observer.data_access.models import (
    IssueTestResultAttachmentRuleExecutionMetadata,
    TestExecutionMetadata,
)
from collections.abc import Sequence


class MinimalIssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: IssueSource
    project: str
    key: str
    title: str
    status: IssueStatus
    url: HttpUrl


class MinimalIssueTestResultAttachmentRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    enabled: bool

    families: list[FamilyName]
    environment_names: list[str]
    test_case_names: list[str]
    template_ids: list[str]
    execution_metadata: ExecutionMetadata

    @field_validator("execution_metadata", mode="before")
    @classmethod
    def convert_execution_metadata(
        cls,
        metadata: Sequence[IssueTestResultAttachmentRuleExecutionMetadata]
        | ExecutionMetadata,
    ) -> ExecutionMetadata:
        if not isinstance(metadata, ExecutionMetadata):
            return ExecutionMetadata.from_rows(
                [
                    TestExecutionMetadata(category=item.category, value=item.value)
                    for item in metadata
                ]
            )

        return metadata


class MinimalIssueTestResultAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    issue: MinimalIssueResponse = Field(validation_alias=AliasPath("issue"))
    attachment_rule: MinimalIssueTestResultAttachmentRuleResponse | None = Field(
        validation_alias=AliasPath("attachment_rule")
    )
