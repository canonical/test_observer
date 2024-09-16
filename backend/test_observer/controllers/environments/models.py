from datetime import datetime

from pydantic import BaseModel, HttpUrl, field_validator

from test_observer.common.constants import VALID_ISSUE_HOSTS


class ReportedIssueRequest(BaseModel):
    environment_name: str
    description: str
    url: HttpUrl
    is_confirmed: bool

    @field_validator("url")
    @classmethod
    def name_must_contain_space(
        cls: type["ReportedIssueRequest"], url: HttpUrl
    ) -> HttpUrl:
        if url.host not in VALID_ISSUE_HOSTS:
            raise ValueError(f"Issue url must belong to one of {VALID_ISSUE_HOSTS}")
        return url


class ReportedIssueResponse(BaseModel):
    id: int
    environment_name: str
    description: str
    url: HttpUrl
    is_confirmed: bool
    created_at: datetime
    updated_at: datetime
