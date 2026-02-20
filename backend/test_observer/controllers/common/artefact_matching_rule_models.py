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

"""
Shared Pydantic models for ArtefactMatchingRule across different API controllers.

This module provides base models that can be used by both the teams API and 
artefact-matching-rules API to avoid duplication while maintaining proper 
OpenAPI schema generation.
"""

from pydantic import BaseModel

from test_observer.data_access.models_enums import FamilyName


class ArtefactMatchingRuleBase(BaseModel):
    """Base model for artefact matching rule with common fields"""
    family: FamilyName
    stage: str | None = None
    track: str | None = None
    branch: str | None = None


class ArtefactMatchingRuleInResponse(BaseModel):
    """Artefact matching rule fields when included in responses (no relationships)"""
    id: int
    family: FamilyName
    stage: str | None
    track: str | None
    branch: str | None
