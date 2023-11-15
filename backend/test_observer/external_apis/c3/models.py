from enum import Enum
from typing import List

from pydantic import BaseModel


class SubmissionProcessingStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class SubmissionStatus(BaseModel):
    id: int
    status: SubmissionProcessingStatus | None
    report_id: int | None


class TestResult(BaseModel):
    id: int
    name: str
    type: str
    status: str
    comments: str
    io_log: str


class Report(BaseModel):
    id: int
    failed_test_count: int
    test_count: int
    test_results: List[TestResult]
