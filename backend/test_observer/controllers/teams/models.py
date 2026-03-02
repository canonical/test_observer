# Copyright 2025 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from pydantic import BaseModel

from test_observer.common.permissions import Permission


class TeamMinimalResponse(BaseModel):
    id: int
    name: str
    permissions: list[str]
    reviewer_families: list[str] = []


class UserMinimalResponse(BaseModel):
    id: int
    launchpad_handle: str | None = None
    email: str
    name: str
    is_admin: bool


class TeamResponse(BaseModel):
    id: int
    name: str
    permissions: list[str]
    reviewer_families: list[str] = []
    members: list[UserMinimalResponse]


class TeamPatch(BaseModel):
    permissions: list[Permission] | None = None
    reviewer_families: list[str] | None = None


class TeamCreate(BaseModel):
    name: str
    permissions: list[Permission] = []
    reviewer_families: list[str] = []
