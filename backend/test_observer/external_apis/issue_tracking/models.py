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

from pydantic import BaseModel

from test_observer.data_access.models_enums import IssueStatus


class IssueInfo(BaseModel):
    """Information about an external issue"""
    
    external_id: str
    title: str
    status: IssueStatus
    url: str
    last_updated: datetime | None = None
    assignee: str | None = None
    labels: list[str] = []
    description: str | None = None


class ParsedIssueURL(BaseModel):
    """Parsed components of an issue URL"""
    
    platform: str  # "github", "jira", "launchpad"
    host: str
    external_id: str
    owner: str | None = None  # GitHub repo owner
    repo: str | None = None   # GitHub repo name
    project: str | None = None  # Jira project key