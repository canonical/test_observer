from datetime import datetime

from pydantic import BaseModel, HttpUrl


class ReportedIssueRequest(BaseModel):
    environment_name: str
    description: str
    url: HttpUrl


class ReportedIssueResponse(BaseModel):
    id: int
    environment_name: str
    description: str
    url: HttpUrl
    created_at: datetime
    updated_at: datetime
