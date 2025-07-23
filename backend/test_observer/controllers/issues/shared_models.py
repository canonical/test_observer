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

from pydantic import BaseModel, HttpUrl
from test_observer.data_access.models_enums import IssueSource, IssueStatus

from pydantic import ConfigDict, Field, AliasPath


class MinimalIssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: IssueSource
    project: str
    key: str
    title: str
    status: IssueStatus
    url: HttpUrl


class MinimalIssueTestResultAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    issue: MinimalIssueResponse = Field(validation_alias=AliasPath("issue"))
