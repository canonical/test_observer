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

from pydantic import BaseModel, HttpUrl, field_validator, model_validator

from test_observer.common.constants import VALID_ISSUE_HOSTS
from test_observer.data_access.models_enums import IssueStatus, IssueSyncStatus


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
    # Issue tracking fields
    external_id: str | None = None
    issue_status: IssueStatus = IssueStatus.UNKNOWN
    sync_status: IssueSyncStatus = IssueSyncStatus.NEVER_SYNCED
    last_synced_at: datetime | None = None
    sync_error: str | None = None
