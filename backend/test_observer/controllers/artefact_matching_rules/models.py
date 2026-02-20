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

from test_observer.data_access.models_enums import FamilyName
from test_observer.controllers.common.artefact_matching_rule_models import (
    ArtefactMatchingRuleBase,
)


class TeamMinimal(BaseModel):
    id: int
    name: str


class ArtefactMatchingRuleResponse(BaseModel):
    """Artefact matching rule with associated teams"""
    id: int
    family: FamilyName
    stage: str | None
    track: str | None
    branch: str | None
    teams: list[TeamMinimal]


class ArtefactMatchingRuleRequest(ArtefactMatchingRuleBase):
    """Request to create an artefact matching rule (extends base with team_ids)"""
    team_ids: list[int]  # At least one team required


class ArtefactMatchingRulePatch(BaseModel):
    """Patch request for artefact matching rule"""
    family: FamilyName | None = None
    stage: str | None = None
    track: str | None = None
    branch: str | None = None
    team_ids: list[int] | None = None  # Optional in patch, but must not be empty if provided
