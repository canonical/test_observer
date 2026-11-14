# Copyright 2024 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import itertools
import logging
from collections.abc import Sequence
from typing import TypedDict

from test_observer.data_access.models import Artefact
from test_observer.data_access.models_enums import FamilyName
from test_observer.external_apis.archive import ArchiveManager
from test_observer.external_apis.snapcraft import (
    get_channel_map_from_snapcraft,
)

logger = logging.getLogger("test-observer-backend")
_SNAP_RISK_ORDER = ("edge", "beta", "candidate", "stable")
_DEB_POCKET_ORDER = ("proposed", "updates")
_POCKET_PROMOTION_MAP = {
    # pocket -> next-pocket
    "proposed": "updates",
    "updates": "updates",
}


class PromotionUpdate(TypedDict, total=False):
    stage: str
    archived: bool


def process_artefact_promotions(
    snap_artefacts: Sequence[Artefact],
    deb_artefacts: Sequence[Artefact],
) -> tuple[dict[int, bool | None], dict[int, str], dict[int, PromotionUpdate]]:
    """
    Fetch promotion data for all artefacts via HTTP. Does not write to the database.

    :snap_artefacts: Snap Artefact objects (detached from any session)
    :deb_artefacts: Deb Artefact objects (detached from any session)
    :return: processed statuses, error messages, and update values keyed by artefact ID
    """
    processed_artefacts_status: dict[int, bool | None] = {}
    processed_artefacts_error_messages: dict[int, str] = {}
    promotion_updates: dict[int, PromotionUpdate] = {}

    for snap in snap_artefacts:
        if snap.stage not in _SNAP_RISK_ORDER:
            processed_artefacts_status[snap.id] = None
            continue
        try:
            new_stage = fetch_snap_promotion(snap)
            promotion_updates[snap.id] = _apply_snap_promotion(snap, new_stage)
            processed_artefacts_status[snap.id] = True
        except Exception as exc:
            processed_artefacts_status[snap.id] = False
            processed_artefacts_error_messages[snap.id] = str(exc)
            logger.warning("Failed to process artefact %s: %s", snap.id, exc, exc_info=True)

    for deb in deb_artefacts:
        try:
            result = fetch_deb_promotion(deb)
            if result is None:
                processed_artefacts_status[deb.id] = None
                continue
            promotion_updates[deb.id] = _apply_deb_promotion(deb, result)
            processed_artefacts_status[deb.id] = True
        except Exception as exc:
            processed_artefacts_status[deb.id] = False
            processed_artefacts_error_messages[deb.id] = str(exc)
            logger.warning("Failed to process artefact %s: %s", deb.id, exc, exc_info=True)

    return processed_artefacts_status, processed_artefacts_error_messages, promotion_updates


def fetch_snap_promotion(snap: Artefact) -> str | None:
    """Fetch snap promotion data from Snapcraft. Returns new stage, or None to archive."""
    assert snap.family == FamilyName.snap
    assert snap.store, f"Store is not set for the snap artefact {snap.id}"

    all_channel_maps = get_channel_map_from_snapcraft(
        snapstore=snap.store,
        snap_name=snap.name,
    )

    matching_channel_maps = [
        cm
        for cm in all_channel_maps
        if cm.channel.track == snap.track
        and cm.channel.architecture in snap.architectures
        and cm.version == snap.version
    ]
    known_risks = [cm.channel.risk for cm in matching_channel_maps if cm.channel.risk in _SNAP_RISK_ORDER]
    if known_risks:
        return max(known_risks, key=_SNAP_RISK_ORDER.index)
    if matching_channel_maps:
        return snap.stage  # Unknown upstream risks must not cause the snap to be archived.
    return None  # no matching channel map — archive the snap


def _apply_snap_promotion(snap: Artefact, new_stage: str | None) -> PromotionUpdate:
    if new_stage is None:
        snap.archived = True
        return {"archived": True}

    snap.stage = new_stage
    return {"stage": new_stage}


def fetch_deb_promotion(artefact: Artefact) -> tuple[bool, str | None] | None:
    """Fetch deb promotion data from the Ubuntu archive.

    Returns (name_found, highest_pocket_found), or None if no HTTP call is needed.
    """
    series = artefact.series
    repo = artefact.repo
    assert series is not None, f"Series is not set for the artefact {artefact.id}"
    assert repo is not None, f"Repo is not set for the artefact {artefact.id}"

    if artefact.stage not in _DEB_POCKET_ORDER:
        return None  # nothing to do yet

    name_found = False
    highest_pocket_found: str | None = None
    for arch, pocket in itertools.product(artefact.architectures, _POCKET_PROMOTION_MAP):
        with ArchiveManager(
            arch=arch,
            series=series,
            pocket=pocket,
            apt_repo=repo,
        ) as archivemanager:
            deb_version = archivemanager.get_deb_version(artefact.name)

        if deb_version:
            name_found = True

            if deb_version == artefact.version and (
                highest_pocket_found is None
                or _DEB_POCKET_ORDER.index(pocket) > _DEB_POCKET_ORDER.index(highest_pocket_found)
            ):
                highest_pocket_found = pocket

    return name_found, highest_pocket_found


def _apply_deb_promotion(artefact: Artefact, result: tuple[bool, str | None]) -> PromotionUpdate:
    name_found, highest_pocket_found = result
    artefact.archived = name_found and not highest_pocket_found
    update: PromotionUpdate = {"archived": artefact.archived}
    if highest_pocket_found is not None:
        artefact.stage = highest_pocket_found
        update["stage"] = highest_pocket_found
    return update
