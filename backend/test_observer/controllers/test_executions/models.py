# Copyright 2023 Canonical Ltd.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Written by:
#        Omar Selo <omar.selo@canonical.com>


from datetime import datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import (
    AliasPath,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
)

from test_observer.common.constants import PREVIOUS_TEST_RESULT_COUNT
from test_observer.data_access.models_enums import (
    FamilyName,
    StageName,
    TestExecutionStatus,
    TestResultStatus,
)


class _StartTestExecutionRequest(BaseModel):
    name: str
    version: str
    arch: str
    environment: str
    ci_link: Annotated[str, HttpUrl] | None = None
    test_plan: str = Field(max_length=200)
    initial_status: TestExecutionStatus = TestExecutionStatus.IN_PROGRESS

    @field_validator("version")
    @classmethod
    def validate_version(cls: type["_StartTestExecutionRequest"], version: str) -> str:
        if version in ("", "null"):
            raise ValueError(f"Invalid version value '{version}'")
        return version


class StartSnapTestExecutionRequest(_StartTestExecutionRequest):
    family: Literal[FamilyName.snap]
    revision: int
    track: str
    store: str
    execution_stage: Literal[StageName.edge] | Literal[StageName.beta] | Literal[
        StageName.candidate
    ] | Literal[StageName.stable]


class StartDebTestExecutionRequest(_StartTestExecutionRequest):
    family: Literal[FamilyName.deb]
    series: str
    repo: str
    execution_stage: Literal[StageName.proposed] | Literal[StageName.updates]


class StartCharmTestExecutionRequest(_StartTestExecutionRequest):
    family: Literal[FamilyName.charm]
    revision: int
    track: str
    execution_stage: Literal[StageName.edge] | Literal[StageName.beta] | Literal[
        StageName.candidate
    ] | Literal[StageName.stable]


class C3TestResultStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"


class C3TestResult(BaseModel):
    name: str
    template_id: str | None = None
    status: C3TestResultStatus
    category: str
    comment: str
    io_log: str


class TestResultRequest(BaseModel):
    name: str
    status: TestResultStatus
    template_id: str = ""
    category: str = ""
    comment: str = ""
    io_log: str = ""


class EndTestExecutionRequest(BaseModel):
    ci_link: Annotated[str, HttpUrl]
    c3_link: Annotated[str, HttpUrl] | None = None
    checkbox_version: str | None = None
    test_results: list[C3TestResult]


class TestExecutionsPatchRequest(BaseModel):
    __test__ = False

    c3_link: HttpUrl | None = None
    ci_link: HttpUrl | None = None
    status: TestExecutionStatus | Literal["COMPLETED"] | None = None


class PreviousTestResult(BaseModel):
    status: TestResultStatus
    version: str
    artefact_id: int


class TestResultResponse(BaseModel):
    __test__ = False

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = Field(validation_alias=AliasPath("test_case", "name"))
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


class RerunRequest(BaseModel):
    test_execution_ids: set[int]


class PendingRerun(BaseModel):
    test_execution_id: int
    ci_link: str = Field(validation_alias=AliasPath("test_execution", "ci_link"))
    family: FamilyName = Field(
        validation_alias=AliasPath(
            "test_execution", "artefact_build", "artefact", "family"
        )
    )


class DeleteReruns(BaseModel):
    test_execution_ids: set[int]


class TestEventDTO(BaseModel):
    event_name: str
    timestamp: datetime
    detail: str


class StatusUpdateRequest(BaseModel):
    events: list[TestEventDTO]
