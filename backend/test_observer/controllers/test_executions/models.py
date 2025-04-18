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
from test_observer.controllers.artefacts.models import (
    ArtefactBuildMinimalResponse,
    ArtefactResponse,
    TestExecutionResponse,
)
from test_observer.data_access.models_enums import (
    FamilyName,
    SnapStage,
    DebStage,
    CharmStage,
    ImageStage,
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
    branch: str | None = ""
    execution_stage: SnapStage


class StartDebTestExecutionRequest(_StartTestExecutionRequest):
    family: Literal[FamilyName.deb]
    series: str
    repo: str
    execution_stage: DebStage


class StartCharmTestExecutionRequest(_StartTestExecutionRequest):
    family: Literal[FamilyName.charm]
    revision: int
    track: str
    branch: str | None = ""
    execution_stage: CharmStage


class StartImageTestExecutionRequest(_StartTestExecutionRequest):
    family: Literal[FamilyName.image] = FamilyName.image
    execution_stage: ImageStage
    os: str
    release: str
    sha256: str
    owner: str
    image_url: HttpUrl


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
    ci_link: str | None = Field(validation_alias=AliasPath("test_execution", "ci_link"))
    family: FamilyName = Field(
        validation_alias=AliasPath(
            "test_execution", "artefact_build", "artefact", "family"
        )
    )
    test_execution: TestExecutionResponse = Field(
        validation_alias=AliasPath("test_execution")
    )
    artefact: ArtefactResponse = Field(
        validation_alias=AliasPath("test_execution", "artefact_build", "artefact")
    )
    artefact_build: ArtefactBuildMinimalResponse = Field(
        validation_alias=AliasPath("test_execution", "artefact_build")
    )


class DeleteReruns(BaseModel):
    test_execution_ids: set[int]


class TestEventResponse(BaseModel):
    event_name: str
    timestamp: datetime
    detail: str


class StatusUpdateRequest(BaseModel):
    events: list[TestEventResponse]
