# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl

from test_observer.controllers.execution_metadata.models import ExecutionMetadata
from test_observer.data_access.models_enums import (
    FamilyName,
    IssueSource,
    IssueStatus,
    TestExecutionStatus,
    TestResultStatus,
)


class SearchPageTableIssue(BaseModel):
    """Compact issue summary for a Search row; detail fields are omitted."""

    id: int
    key: str
    title: str


class SearchPageTableTestResult(BaseModel):
    id: int
    name: str
    category: str
    created_at: datetime
    template_id: str
    status: TestResultStatus
    issues: list[SearchPageTableIssue]


class SearchPageTableEnvironment(BaseModel):
    name: str


class SearchPageTableExecutionMetadata(BaseModel):
    """One literal category/value pair, returned in deterministic order."""

    category: str
    value: str


class SearchPageTableTestExecution(BaseModel):
    id: int
    status: TestExecutionStatus
    environment: SearchPageTableEnvironment
    test_plan: str
    rerun_is_requested: bool = Field(
        description=(
            "Whether a rerun request exists for this execution's test-plan, artefact-build, and environment group."
        )
    )
    execution_is_latest: bool = Field(
        description=(
            "True when no higher-ID test execution exists in the same test-plan, artefact-build, and environment group."
        )
    )
    execution_metadata: list[SearchPageTableExecutionMetadata]


class SearchPageTableReviewer(BaseModel):
    """Compact reviewer summary; email and other user profile fields are omitted."""

    id: int
    name: str
    launchpad_handle: str | None


class SearchPageTableArtefact(BaseModel):
    id: int
    name: str
    version: str
    track: str
    family: FamilyName
    stage: str = Field(
        description="An empty string represents an explicitly empty artefact stage; this field is not null."
    )
    archived: bool
    reviewers: list[SearchPageTableReviewer]


class SearchPageTableArtefactBuild(BaseModel):
    architecture: str


class SearchPageTableRow(BaseModel):
    test_result: SearchPageTableTestResult
    test_execution: SearchPageTableTestExecution
    artefact: SearchPageTableArtefact
    artefact_build: SearchPageTableArtefactBuild


class SearchPageTableResponse(BaseModel):
    """Compact rows for the Search grid, without the on-demand Details payload."""

    count: int | None
    limit: int
    offset: int
    rows: list[SearchPageTableRow]


class SearchPageDetailsIssue(BaseModel):
    id: int
    source: IssueSource
    project: str
    key: str
    title: str
    status: IssueStatus
    url: HttpUrl


class SearchPageDetailsIssueAttachment(BaseModel):
    issue: SearchPageDetailsIssue


class SearchPageDetailsTestResult(BaseModel):
    id: int
    name: str
    category: str
    template_id: str
    status: TestResultStatus
    io_log: str
    issues: list[SearchPageDetailsIssueAttachment]


class SearchPageDetailsTestExecution(BaseModel):
    id: int
    status: TestExecutionStatus
    environment: SearchPageTableEnvironment
    test_plan: str
    created_at: datetime
    execution_metadata: ExecutionMetadata


class SearchPageDetailsArtefact(BaseModel):
    id: int
    name: str
    version: str
    track: str
    family: FamilyName


class SearchPageDetailsArtefactBuild(BaseModel):
    architecture: str


class SearchPageDetailsResponse(BaseModel):
    test_result: SearchPageDetailsTestResult
    test_execution: SearchPageDetailsTestExecution
    artefact: SearchPageDetailsArtefact
    artefact_build: SearchPageDetailsArtefactBuild
