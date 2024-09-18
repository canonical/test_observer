from datetime import datetime

from pydantic import BaseModel, HttpUrl, field_validator

from test_observer.common.constants import VALID_ISSUE_HOSTS


class EnvironmentReportedIssueRequest(BaseModel):
    environment_name: str
    description: str
    url: HttpUrl
    is_confirmed: bool

    @field_validator("url")
    @classmethod
    def url_host_must_be_allowed(
        cls: type["EnvironmentReportedIssueRequest"], url: HttpUrl
    ) -> HttpUrl:
        if url.host not in VALID_ISSUE_HOSTS:
            raise ValueError(f"Issue url must belong to one of {VALID_ISSUE_HOSTS}")
        return url


class EnvironmentReportedIssueResponse(BaseModel):
    id: int
    environment_name: str
    description: str
    url: HttpUrl
    is_confirmed: bool
    created_at: datetime
    updated_at: datetime
