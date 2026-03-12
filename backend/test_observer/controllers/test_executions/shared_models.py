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

from pydantic import AliasPath, BaseModel, ConfigDict, Field

from test_observer.common.constants import PREVIOUS_TEST_RESULT_COUNT
from test_observer.controllers.issues.shared_models import (
    MinimalIssueTestResultAttachmentResponse,
)
from test_observer.data_access.models_enums import TestResultStatus


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
