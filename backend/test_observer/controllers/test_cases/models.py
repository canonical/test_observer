from datetime import datetime

from pydantic import BaseModel, HttpUrl, model_validator


class ReportedIssueRequest(BaseModel):
    template_id: str = ""
    case_name: str = ""
    description: str
    url: HttpUrl

    @model_validator(mode="after")
    def check_a_or_b(self):
        if not self.case_name and not self.template_id:
            raise ValueError("Either case_name or template_id is required")
        return self


class ReportedIssueResponse(BaseModel):
    id: int
    template_id: str = ""
    case_name: str = ""
    description: str
    url: HttpUrl
    created_at: datetime
    updated_at: datetime
