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
