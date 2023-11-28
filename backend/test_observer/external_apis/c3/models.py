from enum import Enum

from pydantic import AliasPath, BaseModel, Field


class SubmissionProcessingStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class SubmissionStatus(BaseModel):
    id: int
    status: SubmissionProcessingStatus | None
    report_id: int | None


class TestResultStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"


class TestResult(BaseModel):
    id: int = Field(validation_alias=AliasPath("test", "id"))
    name: str = Field(validation_alias=AliasPath("test", "name"))
    status: TestResultStatus
    comment: str
    io_log: str


class Report(BaseModel):
    id: int
    failed_test_count: int
    test_results: list[TestResult] = Field(validation_alias="testresult_set")
