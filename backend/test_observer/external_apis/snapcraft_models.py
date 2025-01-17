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
