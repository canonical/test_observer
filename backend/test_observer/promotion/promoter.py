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

from test_observer.data_access.models import Artefact
from test_observer.data_access.models_enums import FamilyName, StageName
from test_observer.external_apis.archive import ArchiveManager
from test_observer.external_apis.snapcraft import (
    get_channel_map_from_snapcraft,
)

logger = logging.getLogger("test-observer-backend")
POCKET_PROMOTION_MAP = {
    # pocket -> next-pocket
    "proposed": StageName.updates,
    "updates": StageName.updates,
}


def process_artefact_promotions(
    snap_artefacts: Sequence[Artefact],
    deb_artefacts: Sequence[Artefact],
) -> tuple[dict[str, bool], dict[str, str]]:
    """
    Fetch promotion data for all artefacts via HTTP. Does not write to the database.

    :snap_artefacts: Snap Artefact objects (detached from any session)
    :deb_artefacts: Deb Artefact objects (detached from any session)
    :return: tuple of (processed statuses, error messages) keyed by artefact identifier
    """
    processed_artefacts_status: dict[str, bool] = {}
    processed_artefacts_error_messages: dict[str, str] = {}

    for snap in snap_artefacts:
        artefact_key = f"{FamilyName.snap} - {snap.name} - {snap.version}"
        try:
            processed_artefacts_status[artefact_key] = True
            new_stage = fetch_snap_promotion(snap)
            _apply_snap_promotion(snap, new_stage)
        except Exception as exc:
            processed_artefacts_status[artefact_key] = False
            processed_artefacts_error_messages[artefact_key] = str(exc)
            logger.warning("WARNING: %s", str(exc), exc_info=True)

    for deb in deb_artefacts:
        artefact_key = f"{FamilyName.deb} - {deb.name} - {deb.version}"
        try:
            processed_artefacts_status[artefact_key] = True
            result = fetch_deb_promotion(deb)
            if result is not None:
                _apply_deb_promotion(deb, result)
        except Exception as exc:
            processed_artefacts_status[artefact_key] = False
            processed_artefacts_error_messages[artefact_key] = str(exc)
            logger.warning("WARNING: %s", str(exc), exc_info=True)

    return processed_artefacts_status, processed_artefacts_error_messages


def fetch_snap_promotion(snap: Artefact) -> StageName | None:
    """Fetch snap promotion data from Snapcraft. Returns new stage, or None to archive."""
    assert snap.family == FamilyName.snap
    assert snap.store, f"Store is not set for the snap artefact {snap.id}"

    all_channel_maps = get_channel_map_from_snapcraft(
        snapstore=snap.store,
        snap_name=snap.name,
    )

    try:
        return max(
            (
                cm.channel.risk
                for cm in all_channel_maps
                if cm.channel.track == snap.track
                and cm.channel.architecture in snap.architectures
                and cm.version == snap.version
            ),
        )
    except ValueError:
        return None  # no matching channel map — archive the snap


def _apply_snap_promotion(snap: Artefact, new_stage: StageName | None) -> None:
    if new_stage is None:
        snap.archived = True
    else:
        snap.stage = new_stage


def fetch_deb_promotion(artefact: Artefact) -> tuple[bool, StageName | None] | None:
    """Fetch deb promotion data from the Ubuntu archive.

    Returns (name_found, highest_pocket_found), or None if no HTTP call is needed.
    """
    series = artefact.series
    repo = artefact.repo
    assert series is not None, f"Series is not set for the artefact {artefact.id}"
    assert repo is not None, f"Repo is not set for the artefact {artefact.id}"

    if not artefact.stage:
        return None  # nothing to do yet

    name_found = False
    highest_pocket_found: None | StageName = None
    for arch, pocket in itertools.product(artefact.architectures, POCKET_PROMOTION_MAP):
        with ArchiveManager(
            arch=arch,
            series=series,
            pocket=pocket,
            apt_repo=repo,
        ) as archivemanager:
            deb_version = archivemanager.get_deb_version(artefact.name)

        if deb_version:
            name_found = True

            if deb_version == artefact.version:
                highest_pocket_found = max(highest_pocket_found or StageName(pocket), StageName(pocket))

    return name_found, highest_pocket_found


def _apply_deb_promotion(artefact: Artefact, result: tuple[bool, StageName | None]) -> None:
    name_found, highest_pocket_found = result
    artefact.archived = name_found and not highest_pocket_found
    artefact.stage = highest_pocket_found or artefact.stage
