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

from pydantic import BaseModel

from test_observer.controllers.execution_metadata.models import ExecutionMetadata
from test_observer.data_access.models_enums import FamilyName, TestExecutionStatus, TestResultStatus


class SearchPageTableTestResult(BaseModel):
    id: int
    name: str
    category: str
    created_at: datetime
    template_id: str
    status: TestResultStatus


class SearchPageTableEnvironment(BaseModel):
    name: str


class SearchPageTableTestExecution(BaseModel):
    id: int
    status: TestExecutionStatus
    is_rerun_requested: bool
    environment: SearchPageTableEnvironment
    test_plan: str
    execution_metadata: ExecutionMetadata


class SearchPageTableArtefact(BaseModel):
    id: int
    name: str
    version: str
    track: str
    family: FamilyName


class SearchPageTableArtefactBuild(BaseModel):
    architecture: str


class SearchPageTableRow(BaseModel):
    test_result: SearchPageTableTestResult
    test_execution: SearchPageTableTestExecution
    artefact: SearchPageTableArtefact
    artefact_build: SearchPageTableArtefactBuild


class SearchPageTableResponse(BaseModel):
    count: int | None
    limit: int
    offset: int
    rows: list[SearchPageTableRow]


class SearchPageDetailsIssue(BaseModel):
    id: int
    source: str
    project: str
    key: str
    title: str
    status: str
    url: str


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
