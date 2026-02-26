# Copyright 2023 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import logging

import requests

from .snapcraft_models import ChannelMap, SnapInfo, rename_keys

logger = logging.getLogger("test-observer-backend")


def get_channel_map_from_snapcraft(snapstore: str, snap_name: str) -> list[ChannelMap]:
    """
    Get channel_map from snapcraft.io

    :snapstore: Snapstore name
    :snap_name: snap name
    :return: channgel map as python dict (JSON format)
    """
    headers = {
        "Snap-Device-Series": "16",
        "Snap-Device-Store": snapstore,
    }
    req = requests.get(
        f"https://api.snapcraft.io/v2/snaps/info/{snap_name}",
        headers=headers,
        timeout=10,  # 10 seconds
    )
    json_resp = req.json()
    if not req.ok:
        logger.error(json_resp["error-list"][0]["message"])
        req.raise_for_status()

    snap_info = SnapInfo(**rename_keys(json_resp))
    return snap_info.channel_map
