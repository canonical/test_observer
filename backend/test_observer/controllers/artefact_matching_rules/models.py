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
#
# SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from pydantic import BaseModel

from test_observer.common.enums import Permission
from test_observer.data_access.models_enums import FamilyName


class ArtefactMatchingRuleBase(BaseModel):
    """Base model for artefact matching rule with common fields"""

    name: str = ""
    family: FamilyName
    stage: str = ""
    track: str = ""
    branch: str = ""
    store: str = ""
    series: str = ""
    os: str = ""
    release: str = ""
    owner: str = ""


class ArtefactMatchingRuleInResponse(BaseModel):
    """Artefact matching rule fields when included in responses (no relationships)"""

    id: int
    name: str | None
    family: FamilyName
    stage: str | None
    track: str | None
    branch: str | None
    store: str | None
    series: str | None
    os: str | None
    release: str | None
    owner: str | None
    grant_permissions: list[Permission]


class TeamMinimal(BaseModel):
    id: int
    name: str


class ArtefactMatchingRuleResponse(BaseModel):
    """Artefact matching rule with associated teams"""

    id: int
    name: str | None
    family: FamilyName
    stage: str | None
    track: str | None
    branch: str | None
    store: str | None
    series: str | None
    os: str | None
    release: str | None
    owner: str | None
    teams: list[TeamMinimal]
    grant_permissions: list[Permission]


class ArtefactMatchingRuleRequest(ArtefactMatchingRuleBase):
    """Request to create an artefact matching rule (extends base with team_ids)"""

    team_ids: list[int]  # At least one team required
    grant_permissions: list[Permission] = []


class ArtefactMatchingRulePatch(BaseModel):
    """Patch request for artefact matching rule"""

    name: str | None = None
    family: FamilyName | None = None
    stage: str | None = None
    track: str | None = None
    branch: str | None = None
    store: str | None = None
    series: str | None = None
    os: str | None = None
    release: str | None = None
    owner: str | None = None
    team_ids: list[int] | None = None  # Optional in patch, but must not be empty if provided
    grant_permissions: list[Permission] | None = None
