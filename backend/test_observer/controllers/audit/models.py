# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


class AuditAuthorResponse(BaseModel):
    user_id: int | None
    application_id: int | None
    automation_name: str | None


class AuditListItemResponse(BaseModel):
    id: int
    created_at: datetime
    author: AuditAuthorResponse


class AuditHistoryResponse(BaseModel):
    entries: list[AuditListItemResponse]
    count: int
    limit: int
    offset: int


class AuditDetailResponse(BaseModel):
    id: int
    operation: Literal["I", "U", "D"]
    created_at: datetime
    author: AuditAuthorResponse
    data: dict[str, Any]
