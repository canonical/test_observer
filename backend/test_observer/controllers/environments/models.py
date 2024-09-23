from datetime import datetime

from pydantic import BaseModel, HttpUrl, model_validator

from test_observer.common.constants import VALID_ISSUE_HOSTS


class EnvironmentReportedIssueRequest(BaseModel):
    environment_name: str
    description: str
    url: HttpUrl | None = None
    is_confirmed: bool

    @model_validator(mode="after")
    def validate_url(self) -> "EnvironmentReportedIssueRequest":
        if self.url is None and self.is_confirmed:
            raise ValueError("A URL is required if the issue is confirmed")

        if self.url is not None and self.url.host not in VALID_ISSUE_HOSTS:
            raise ValueError(f"Issue url must belong to one of {VALID_ISSUE_HOSTS}")

        return self


class EnvironmentReportedIssueResponse(BaseModel):
    id: int
    environment_name: str
    description: str
    url: HttpUrl | None
    is_confirmed: bool
    created_at: datetime
    updated_at: datetime
