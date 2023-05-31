import logging
import sys

import requests

from .snapcraft_models import SnapInfo, rename_keys

logger = logging.getLogger("test-observer-backend")


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

    snap_info = SnapInfo(**rename_keys(json_resp))
    return snap_info.channel_map
