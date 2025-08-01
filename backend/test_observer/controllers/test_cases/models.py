from datetime import datetime

from pydantic import BaseModel, HttpUrl, field_validator, model_validator

from test_observer.common.constants import VALID_ISSUE_HOSTS


class TestReportedIssueRequest(BaseModel):
    template_id: str = ""
    case_name: str = ""
    description: str
    url: HttpUrl

    @model_validator(mode="after")
    def check_a_or_b(self):
        if not self.case_name and not self.template_id:
            raise ValueError("Either case_name or template_id is required")

        return self

    @field_validator("url")
    @classmethod
    def name_must_contain_space(
        cls: type["TestReportedIssueRequest"], url: HttpUrl
    ) -> HttpUrl:
        if url.host not in VALID_ISSUE_HOSTS:
            raise ValueError(f"Issue url must belong to one of {VALID_ISSUE_HOSTS}")
        return url


class TestReportedIssueResponse(BaseModel):
    id: int
    template_id: str = ""
    case_name: str = ""
    description: str
    url: HttpUrl
    created_at: datetime
    updated_at: datetime


class TestCaseInfo(BaseModel):
    """Model for individual test case information"""

    test_case: str
    template_id: str


class TestCasesResponse(BaseModel):
    """Response model for test cases endpoint - flat list as suggested by Ryan"""

    test_cases: list[TestCaseInfo]
