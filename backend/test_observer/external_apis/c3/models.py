from enum import Enum

from pydantic import BaseModel


class SubmissionProcessingStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class SubmissionStatus(BaseModel):
    id: int
    status: SubmissionProcessingStatus
    report_id: int | None


class Report(BaseModel):
    id: int
    failed_test_count: int