from datetime import datetime

from pydantic import BaseModel, HttpUrl


class ReportedIssueRequest(BaseModel):
    template_id: str
    description: str
    url: HttpUrl


class ReportedIssueResponse(BaseModel):
    id: int
    template_id: str
    description: str
    url: HttpUrl
    created_at: datetime
    updated_at: datetime
