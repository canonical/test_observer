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

from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, Field

# C3 may serialise an unset JSON metadata field as null; treat it as empty.
Metadata = Annotated[dict[str, Any], BeforeValidator(lambda v: {} if v is None else v)]


class TestingPoolEnvironment(BaseModel):
    """A testing environment within a pool.

    ``name`` is the Test Observer environment name (a deb system-id or snap
    environment name); ``queue`` is the Testflinger queue the job dispatches to;
    ``arch`` is the single architecture the environment runs on. Several
    environments may share a queue and arch (e.g. different core bases/flavors).
    """

    name: str
    queue: str
    arch: str
    metadata: Metadata = Field(default_factory=dict)


class TestingPool(BaseModel):
    """A C3 testing pool: the set of environments that validate a single artefact.

    Mirrors the response of C3's ``GET /api/v2/testing-pools/`` endpoint. ``metadata``
    holds structured, family-specific artefact identity (e.g. ``kernel``/``series``/
    ``repo``/``source`` for deb).
    """

    name: str
    family: str
    metadata: Metadata = Field(default_factory=dict)
    environments: list[TestingPoolEnvironment] = Field(default_factory=list)
    description: str = ""
