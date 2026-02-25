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

from pydantic import BaseModel, ConfigDict

from test_observer.controllers.test_executions.shared_models import (
    TestResultResponse,
)
from test_observer.controllers.artefacts.models import (
    TestExecutionResponse,
)
from test_observer.controllers.artefacts.models import (
    ArtefactResponse,
    ArtefactBuildMinimalResponse,
)


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
