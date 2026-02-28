# Copyright 2023 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import (
    AliasPath,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

from test_observer.controllers.artefacts.models import (
    ArtefactBuildMinimalResponse,
    ArtefactResponse,
    TestExecutionRelevantLinkCreate,
    TestExecutionResponse,
)
from test_observer.controllers.execution_metadata.models import ExecutionMetadata
from test_observer.controllers.test_results.shared_models import TestResultSearchFilters
from test_observer.data_access.models_enums import (
    CharmStage,
    DebStage,
    FamilyName,
    ImageStage,
    SnapStage,
    TestExecutionStatus,
    TestResultStatus,
)


class _StartTestExecutionRequest(BaseModel):
    name: str = Field(
        description="User-defined name identifying the artefact under test. "
        "Not unique - multiple versions/stages of the same artefact share this name. "
        "Examples: 'core22', 'ubuntu-desktop', 'snapd'"
    )
    version: str = Field(
        description="Version identifier of the artefact being tested. "
        "Format depends on artefact family - e.g., revisions for "
        "charms/snaps, version numbers for debs."
    )
    arch: str = Field(
        description="CPU architecture where tests will execute. "
        "Common values: 'amd64', 'arm64', 'armhf', 's390x', 'ppc64el'"
    )
    environment: str = Field(
        description="Name of the test execution environment. "
        "This can identify the specific physical device, VM, or "
        "container where tests run or logical environment like a test "
        "lab or cloud region. Examples: 'cm3', 'rpi4', 'lxd-vm', "
        "'aws-ec2'. The environment will be auto-created if it doesn't "
        "exist."
    )
    ci_link: Annotated[str, HttpUrl] | None = Field(
        default=None,
        description="Optional URL linking to the CI job executing these "
        "tests. Useful for tracking test runs back to their automation "
        "source. Can be omitted.",
    )
    test_plan: str = Field(
        max_length=200,
        description="Identifier for the test suite or plan executed. "
        "Groups related test results together - e.g., "
        "'certification-24.04', 'smoke-tests', 'full-regression'. "
        "The test plan will be auto-created if it doesn't exist.",
    )
    initial_status: TestExecutionStatus = Field(
        default=TestExecutionStatus.IN_PROGRESS,
        description="Initial status of the test execution. "
        "Default 'IN_PROGRESS' is appropriate for ongoing tests. "
        "Use 'COMPLETED' if test results will be uploaded separately.",
    )
    relevant_links: list[TestExecutionRelevantLinkCreate] = Field(
        default_factory=list,
        description="Optional list of additional URLs related to this test "
        "execution (e.g., bug reports, documentation, related PRs). Can "
        "be omitted or left empty.",
    )
    needs_assignment: bool = Field(
        default=False,
        description="Whether the artefact created from this test "
        "execution requires assignment of a reviewer. Set to true if "
        "test results need human review before the artefact can be "
        "promoted. Default false means no review assignment needed.",
    )

    @field_validator("version")
    @classmethod
    def validate_version(cls: type["_StartTestExecutionRequest"], version: str) -> str:
        if version in ("", "null"):
            raise ValueError(f"Invalid version value '{version}'")
        return version


class StartSnapTestExecutionRequest(_StartTestExecutionRequest):
    family: Literal[FamilyName.snap]
    revision: int = Field(
        description="Snap package revision number from the store. "
        "Each architecture build has its own revision number. "
        "Find this in the snap store or via 'snap info <snap-name>' command."
    )
    track: str = Field(
        description="Snap release track being tested. "
        "Tracks represent different major versions or streams of "
        "development. Common values: 'latest' (default), version "
        "numbers like '22', '1.0', or custom tracks like "
        "'experimental'. Use 'latest' if unsure."
    )
    store: str = Field(
        description="Snap store where the snap is published. "
        "Typically 'ubuntu' for public Ubuntu Store snaps, or a brand "
        "store ID for enterprise stores. Use 'ubuntu' for standard "
        "snaps."
    )
    branch: str = Field(
        max_length=200,
        default="",
        description="Optional snap branch name within the track/risk "
        "level. Branches are temporary testing channels. Usually empty "
        "string (default) unless testing a specific branch.",
    )
    execution_stage: SnapStage = Field(
        description="Distribution channel/risk level of the snap being "
        "tested. Options: 'edge' (cutting-edge, frequent updates), "
        "'beta' (pre-release testing), 'candidate' (release candidate), "
        "'stable' (production ready). Choose based on where the snap "
        "currently resides in the release pipeline."
    )


class StartDebTestExecutionRequest(_StartTestExecutionRequest):
    family: Literal[FamilyName.deb]
    series: str = Field(
        description="Ubuntu release series being tested. Examples: "
        "'focal' (20.04), 'jammy' (22.04), 'noble' (24.04), 'oracular' "
        "(24.10)"
    )
    repo: str = Field(
        description="Repository containing the deb package. Examples: "
        "'main', 'universe', 'restricted', 'multiverse' for archive "
        "repositories, or custom PPA names like 'ppa:team/ppa-name'"
    )
    source: str = Field(
        max_length=200,
        default="",
        description="Source package name for PPA builds, or empty string "
        "for archive pockets. Provide this OR execution_stage, not both. "
        "Use source when testing from a PPA, use execution_stage when "
        "testing from official archive pockets.",
    )
    execution_stage: DebStage | Literal[""] = Field(
        max_length=100,
        default="",
        description="Archive pocket where the deb resides, or empty "
        "string for PPAs. Options: 'proposed' (pre-release testing "
        "area), 'updates' (stable updates). Provide this OR source, not "
        "both. Use execution_stage for official archive testing, leave "
        "empty if testing from a PPA (and provide source instead).",
    )

    @model_validator(mode="after")
    def one_of_source_or_stage(self) -> Self:
        if not (self.source or self.execution_stage):
            raise ValueError("Received no source or execution_stage")
        if self.source and self.execution_stage:
            raise ValueError("Received both source and execution_stage")
        return self


class StartCharmTestExecutionRequest(_StartTestExecutionRequest):
    family: Literal[FamilyName.charm]
    revision: int = Field(
        description="Charm revision number from Charmhub. "
        "Each architecture build has its own revision. "
        "Find this via 'charm info <charm-name>' or in Charmhub."
    )
    track: str = Field(
        description="Charm release track being tested. "
        "Tracks represent different major versions or development streams. "
        "Common values: 'latest' (default), version-based tracks like '1.0', '22'. "
        "Use 'latest' if unsure."
    )
    branch: str = Field(
        default="",
        description="Optional charm branch name within the track/risk "
        "level. Branches are temporary testing channels. Usually empty "
        "string (default) unless testing a specific branch.",
    )
    execution_stage: CharmStage = Field(
        description="Distribution channel/risk level of the charm being tested. "
        "Options: 'edge' (cutting-edge updates), 'beta' (pre-release), "
        "'candidate' (release candidate), 'stable' (production). "
        "Choose based on where the charm currently resides in the release pipeline."
    )


class StartImageTestExecutionRequest(_StartTestExecutionRequest):
    family: Literal[FamilyName.image] = FamilyName.image
    execution_stage: ImageStage = Field(
        description="Promotion stage of the image being tested. "
        "Options: 'pending' (awaiting approval), 'current' (approved and published). "
        "Use 'pending' for images undergoing testing before promotion."
    )
    os: str = Field(description="Operating system of the image. Examples: 'ubuntu', 'ubuntu-core', 'ubuntu-server'")
    release: str = Field(
        description="OS release codename or version. Examples: 'focal', 'jammy', 'noble', '20.04', '22.04', '24.04'"
    )
    sha256: str = Field(
        description="SHA256 checksum hash uniquely identifying this image build. "
        "Used to verify image integrity and uniqueness."
    )
    owner: str = Field(
        description="Team or organization responsible for the image. Examples: 'canonical', 'ubuntu-images', team names"
    )
    image_url: HttpUrl = Field(
        description="Direct URL where the image file can be downloaded or accessed. Should be a valid HTTP/HTTPS URL."
    )


class C3TestResultStatus(StrEnum):
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
    execution_metadata: ExecutionMetadata | None = None


class RerunRequest(BaseModel):
    test_execution_ids: set[int] = Field(default_factory=set)
    test_results_filters: TestResultSearchFilters | None = None


class PendingRerun(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    test_execution_id: int = Field(validation_alias=AliasPath("test_executions", 0, "id"))
    ci_link: str | None = Field(validation_alias=AliasPath("test_executions", 0, "ci_link"))
    family: FamilyName = Field(validation_alias=AliasPath("artefact_build", "artefact", "family"))
    test_execution: TestExecutionResponse = Field(validation_alias=AliasPath("test_executions", 0))
    artefact: ArtefactResponse = Field(validation_alias=AliasPath("artefact_build", "artefact"))
    artefact_build: ArtefactBuildMinimalResponse = Field(validation_alias=AliasPath("artefact_build"))


class DeleteReruns(BaseModel):
    test_execution_ids: set[int] = Field(default_factory=set)
    test_results_filters: TestResultSearchFilters | None = None


class TestEventResponse(BaseModel):
    event_name: str
    timestamp: datetime
    detail: str


class StatusUpdateRequest(BaseModel):
    events: list[TestEventResponse]
