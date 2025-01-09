# Copyright 2023 Canonical Ltd.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Written by:
#        Nadzeya Hutsko <nadzeya.hutsko@canonical.com>
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
