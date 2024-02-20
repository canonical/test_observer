from typing import Protocol

from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    TestCase,
    TestExecution,
    TestResult,
)
from test_observer.data_access.models_enums import (
    TestExecutionReviewDecision,
    TestExecutionStatus,
    TestResultStatus,
)


class ArtefactBuildCreator(Protocol):
    def __call__(
        self, artefact: Artefact, architecture: str = ..., revision: int | None = ..., /
    ) -> ArtefactBuild: ...


class EnvironmentCreator(Protocol):
    def __call__(self, name: str = ..., architecture: str = ..., /) -> Environment: ...


class TestExecutionCreator(Protocol):
    def __call__(
        self,
        artefact_build: ArtefactBuild,
        environment: Environment,
        ci_link: str | None = ...,
        c3_link: str | None = ...,
        status: TestExecutionStatus = ...,
        review_decision: list[TestExecutionReviewDecision] | None = ...,
        review_comment: str = "",
        /,
    ) -> TestExecution: ...


class TestCaseCreator(Protocol):
    def __call__(self, name: str = ..., category: str = ..., /) -> TestCase: ...


class TestResultCreator(Protocol):
    def __call__(
        self,
        test_case: TestCase,
        test_execution: TestExecution,
        status: TestResultStatus = ...,
        comment: str = ...,
        io_log: str = ...,
        /,
    ) -> TestResult: ...
