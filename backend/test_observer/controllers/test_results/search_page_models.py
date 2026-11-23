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

from pydantic import BaseModel, HttpUrl

from test_observer.controllers.execution_metadata.models import ExecutionMetadata
from test_observer.data_access.models_enums import (
    FamilyName,
    IssueSource,
    IssueStatus,
    TestExecutionStatus,
    TestResultStatus,
)


class SearchPageTestResult(BaseModel):
    id: int
    created_at: datetime
    name: str
    category: str
    status: TestResultStatus


class SearchPageEnvironment(BaseModel):
    name: str


class SearchPageTestExecution(BaseModel):
    id: int
    environment: SearchPageEnvironment
    test_plan: str


class SearchPageArtefact(BaseModel):
    id: int
    name: str
    version: str
    track: str
    family: FamilyName


class SearchPageArtefactBuild(BaseModel):
    architecture: str


class TestResultSearchPageRow(BaseModel):
    test_result: SearchPageTestResult
    test_execution: SearchPageTestExecution
    artefact: SearchPageArtefact
    artefact_build: SearchPageArtefactBuild


class TestResultSearchPage(BaseModel):
    count: int | None
    limit: int
    offset: int
    test_results: list[TestResultSearchPageRow]


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
    environment: SearchPageEnvironment
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
