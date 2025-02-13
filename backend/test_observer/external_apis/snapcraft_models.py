# Copyright (C) 2023-2025 Canonical Ltd.
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


"""Mappings for json objects from snapcraft"""

from typing import Literal

from pydantic import BaseModel

from test_observer.data_access.models_enums import StageName


class Channel(BaseModel):
    architecture: str
    risk: Literal[StageName.edge, StageName.beta, StageName.candidate, StageName.stable]
    track: str


class ChannelMap(BaseModel):
    channel: Channel
    revision: int
    version: str


class SnapInfo(BaseModel):
    channel_map: list[ChannelMap]


def rename_keys(data: list | dict):
    """Replace - with _ in dicts to avoid errors in mapping"""
    if isinstance(data, list):
        return [rename_keys(i) for i in data]
    if isinstance(data, dict):
        return {
            key.replace("-", "_"): rename_keys(value) for key, value in data.items()
        }
    return data
