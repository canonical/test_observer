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

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from test_observer.controllers.test_executions.models import (
    TestResultResponse,
    TestExecutionResponse,
)
from test_observer.controllers.artefacts.models import (
    ArtefactResponse,
    ArtefactBuildMinimalResponse,
)
from test_observer.data_access.models_enums import FamilyName
from test_observer.controllers.execution_metadata.models import ExecutionMetadata


class TestResultSearchResponse(BaseModel):
    """Response model for test results search endpoint"""

    count: int
    test_results: list[TestResultResponse]


class TestResultResponseWithContext(BaseModel):
    """Test result response with artefact and test execution context"""

    model_config = ConfigDict(from_attributes=True)

    test_result: TestResultResponse
    test_execution: TestExecutionResponse
    artefact: ArtefactResponse
    artefact_build: ArtefactBuildMinimalResponse


class TestResultSearchResponseWithContext(BaseModel):
    """Response model for test results search endpoint with full context"""

    count: int
    test_results: list[TestResultResponseWithContext]


class TestResultSearchFilters(BaseModel):
    families: list[FamilyName] = Field(default_factory=list)
    artefacts: list[str] = Field(default_factory=list)
    environments: list[str] = Field(default_factory=list)
    test_cases: list[str] = Field(default_factory=list)
    template_ids: list[str] = Field(default_factory=list)
    execution_metadata: ExecutionMetadata = Field(default_factory=ExecutionMetadata)
    issues: list[int] = Field(default_factory=list)
    from_date: datetime | None = None
    until_date: datetime | None = None
    offset: int | None = None
    limit: int | None = None
