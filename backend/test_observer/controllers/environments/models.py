# Copyright (C) 2023 Canonical Ltd.
#
# This file is part of Test Observer Backend.
#
# Test Observer Backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# Test Observer Backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


from datetime import datetime

from pydantic import BaseModel, HttpUrl, model_validator

from test_observer.common.constants import VALID_ISSUE_HOSTS
from test_observer.data_access.models_enums import IssueStatus, IssueSyncStatus


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
    # Issue tracking fields
    external_id: str | None = None
    issue_status: IssueStatus = IssueStatus.UNKNOWN
    sync_status: IssueSyncStatus = IssueSyncStatus.NEVER_SYNCED
    last_synced_at: datetime | None = None
    sync_error: str | None = None
