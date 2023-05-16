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


import sys
import logging
import requests

from src.services import get_stage_by_name


CHANNEL_PROMOTION_MAP = {
    # channel -> next-channel
    "edge": "beta",
    "beta": "candidate",
    "candidate": "stable",
    "stable": "stable",
}


logger = logging.getLogger("test-observer-backend")


def run_snap_manager(session, artefact, config_dict: dict) -> None:
    """
    Check snap artefacts state and move/archive them if necessary

    :session: DB connection session
    :artefact: an Artefact object
    :config_dict: parsed config file
    """
    arch = config_dict[artefact.name]["arch"]
    channel_map = get_channel_map_from_snapcraft(
        arch=arch,
        snapstore=config_dict[artefact.name]["store"],
        snap_name=artefact.name,
    )
    track = artefact.source.get("track", "latest")
    for channel_info in channel_map:
        if (
            channel_info["channel"]["track"] != track
            or channel_info["channel"]["architecture"] != arch
        ):
            continue
        risk = channel_info["channel"]["risk"]
        try:
            version = channel_info["version"]
            revision = channel_info["revision"]
        except KeyError as exc:
            logger.warning(
                "No key '%s' is found. Continue processing...",
                str(exc),
            )
            continue
        # If the snap with this name in this channel is a
        # different revision, then this is old. So, we archive it
        if risk == artefact.stage.name and revision != artefact.source["revision"]:
            logger.info("Archiving old revision: '%s'", artefact)
            artefact.is_archived = True
            continue
        next_risk = CHANNEL_PROMOTION_MAP[artefact.stage.name]
        if (
            risk == next_risk != artefact.stage.name.lower()
            and version == artefact.version
            and revision == artefact.source["revision"]
        ):
            logger.info("Move artefact '%s' to the '%s' stage", artefact, next_risk)
            artefact.stage = get_stage_by_name(session, next_risk)
            break


def get_channel_map_from_snapcraft(arch: str, snapstore: str, snap_name: str):
    """
    Get channel_map from snapcraft.io

    :arch: architecture
    :snapstore: Snapstore name
    :snap_name: snap name
    :return: channgel map as python dict (JSON format)
    """
    headers = {
        "Snap-Device-Series": "16",
        "Snap-Device-Architecture": arch,
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
        sys.exit(1)
    return json_resp["channel-map"]
