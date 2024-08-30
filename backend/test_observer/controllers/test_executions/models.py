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
from typing import Annotated

from pydantic import (
    AliasPath,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_serializer,
    field_validator,
    model_validator,
)

from test_observer.common.constants import PREVIOUS_TEST_RESULT_COUNT
from test_observer.data_access.models_enums import (
    FamilyName,
    TestExecutionReviewDecision,
    TestExecutionStatus,
    TestResultStatus,
)


class StartTestExecutionRequest(BaseModel):
    family: FamilyName
    name: str
    version: str
    revision: int | None = None
    track: str | None = None
    store: str | None = None
    series: str | None = None
    repo: str | None = None
    arch: str
    execution_stage: str
    environment: str
    ci_link: Annotated[str, HttpUrl]

    @field_serializer("family")
    def serialize_dt(self, family: FamilyName):
        return family.value

    @field_validator("version")
    @classmethod
    def validate_version(cls: type["StartTestExecutionRequest"], version: str) -> str:
        if version in ("", "null"):
            raise ValueError(f"Invalid version value '{version}'")
        return version

    @model_validator(mode="after")
    def validate_required_fields(self) -> "StartTestExecutionRequest":
        required_fields = {
            FamilyName.SNAP: ("store", "track", "revision"),
            FamilyName.DEB: ("series", "repo"),
        }
        family = self.family

        for required_field in required_fields[family]:
            if not getattr(self, required_field):
                raise ValueError(f"{required_field} is required for {family} family")

        return self


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


class EndTestExecutionRequest(BaseModel):
    ci_link: Annotated[str, HttpUrl]
    c3_link: Annotated[str, HttpUrl] | None = None
    checkbox_version: str | None = None
    test_results: list[C3TestResult]


class TestExecutionsPatchRequest(BaseModel):
    __test__ = False

    c3_link: HttpUrl | None = None
    ci_link: HttpUrl | None = None
    status: TestExecutionStatus | None = None
    review_decision: set[TestExecutionReviewDecision] | None = None
    review_comment: str | None = None

    @field_validator("review_decision")
    @classmethod
    def validate_review_decision(
        cls: type["TestExecutionsPatchRequest"],
        review_decision: set[TestExecutionReviewDecision] | None,
    ) -> set[TestExecutionReviewDecision] | None:
        if review_decision is None:
            return review_decision

        if len(review_decision) <= 1:
            return review_decision

        if TestExecutionReviewDecision.REJECTED in review_decision:
            raise ValueError("Test execution can either be rejected or approved")
        return review_decision


class PreviousTestResult(BaseModel):
    status: TestResultStatus
    version: str


class TestResultDTO(BaseModel):
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
            "test_execution", "artefact_build", "artefact", "stage", "family", "name"
        )
    )


class DeleteReruns(BaseModel):
    test_execution_ids: set[int]


class TestEvent(BaseModel):
    event_name: str
    timestamp: datetime
    detail: str


class StatusUpdateRequest(BaseModel):
    events: list[TestEvent]
