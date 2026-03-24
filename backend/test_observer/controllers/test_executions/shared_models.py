# Copyright 2025 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from datetime import datetime
from typing import Literal

from pydantic import AliasPath, BaseModel, ConfigDict, Field, model_validator

from test_observer.common.constants import PREVIOUS_TEST_RESULT_COUNT, QueryValue
from test_observer.controllers.execution_metadata.models import ExecutionMetadata
from test_observer.controllers.issues.shared_models import (
    MinimalIssueTestResultAttachmentResponse,
)
from test_observer.data_access.models_enums import FamilyName, TestExecutionStatus, TestResultStatus


class PreviousTestResult(BaseModel):
    status: TestResultStatus
    version: str
    artefact_id: int
    test_execution_id: int
    test_result_id: int


class TestResultResponse(BaseModel):
    __test__ = False

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = Field(validation_alias=AliasPath("test_case", "name"))
    created_at: datetime
    category: str = Field(validation_alias=AliasPath("test_case", "category"))
    template_id: str = Field(validation_alias=AliasPath("test_case", "template_id"))
    status: TestResultStatus
    comment: str
    io_log: str
    previous_results: list[PreviousTestResult] = Field(
        default=[],
        description=(
            f"The last {PREVIOUS_TEST_RESULT_COUNT} test results matched with "
            "the current test execution. The items are sorted in descending order, "
            "the first test result is the most recent, while "
            "the last one is the oldest one."
        ),
    )
    issues: list[MinimalIssueTestResultAttachmentResponse] = Field(
        validation_alias=AliasPath("issue_attachments"),
    )


class TestExecutionSearchFilters(BaseModel):
    """Filter model for test execution search endpoint."""

    families: list[FamilyName] = Field(default_factory=list)
    artefacts: list[str] = Field(default_factory=list)
    artefact_is_archived: bool | None = None
    environments: list[str] = Field(default_factory=list)
    test_execution_statuses: list[TestExecutionStatus] = Field(default_factory=list)
    execution_metadata: ExecutionMetadata = Field(default_factory=ExecutionMetadata)
    reviewer_ids: list[int] | Literal[QueryValue.ANY, QueryValue.NONE] = Field(default_factory=list)
    assignee_ids: list[int] | Literal[QueryValue.ANY, QueryValue.NONE] | None = Field(
        default=None,
        deprecated=True,
    )
    rerun_is_requested: bool | None = None
    execution_is_latest: bool | None = None
    limit: int = 50
    offset: int = 0

    @model_validator(mode="before")
    @classmethod
    def _migrate_assignee_ids(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data

        reviewer_ids = data.get("reviewer_ids")
        assignee_ids = data.get("assignee_ids")
        if (reviewer_ids is None or reviewer_ids == []) and assignee_ids is not None:
            data["reviewer_ids"] = assignee_ids
        return data
