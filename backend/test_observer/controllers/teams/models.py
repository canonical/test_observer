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
from test_observer.controllers.common.artefact_matching_rule_models import (
    ArtefactMatchingRuleBase,
    ArtefactMatchingRuleInResponse,
)

class TeamMinimalResponse(BaseModel):
    id: int
    name: str
    permissions: list[str]


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
    members: list[UserMinimalResponse]
    artefact_matching_rules: list[ArtefactMatchingRuleInResponse]


class TeamPatch(BaseModel):
    permissions: list[Permission] | None = None
    artefact_matching_rules: list[ArtefactMatchingRuleBase] | None = None


class TeamCreate(BaseModel):
    name: str
    permissions: list[Permission] = []
    artefact_matching_rules: list[ArtefactMatchingRuleBase] = []
