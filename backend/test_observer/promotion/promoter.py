# Copyright (C) 2023 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import logging

from sqlalchemy.orm import Session

from test_observer.data_access.models import Artefact
from test_observer.data_access.models_enums import FamilyName, StageName
from test_observer.data_access.repository import get_artefacts_by_family
from test_observer.external_apis.archive import ArchiveManager
from test_observer.external_apis.snapcraft import (
    get_channel_map_from_snapcraft,
)

logger = logging.getLogger("test-observer-backend")
POCKET_PROMOTION_MAP = {
    # pocket -> next-pocket
    StageName.proposed: StageName.updates,
    StageName.updates: StageName.updates,
}


def promote_artefacts(db: Session):
    """
    Promote all the artefacts in all the families if it has been updated on the
    external source
    """
    try:
        (
            processed_artefacts_status,
            processed_artefacts_error_messages,
        ) = promoter_controller(db)
        logger.info("INFO: Processed artefacts %s", processed_artefacts_status)
        if False in processed_artefacts_status.values():
            logger.error(
                {
                    artefact_key: processed_artefacts_error_messages[artefact_key]
                    for (
                        artefact_key,
                        artefact_status,
                    ) in processed_artefacts_status.items()
                    if artefact_status is False
                }
            )
        return logger.info(
            {"detail": "All the artefacts have been processed successfully"}
        )
    except Exception as exc:
        return logger.error({"detail": str(exc)})


def promoter_controller(session: Session) -> tuple[dict, dict]:
    """
    Orchestrate the snap promoter job

    :session: DB connection session
    :return: tuple of dicts, the first the processed cards and the status of execution
    the second only for the processed cards with the corresponding error message
    """
    family_mapping = {
        FamilyName.snap: run_snap_promoter,
        FamilyName.deb: run_deb_promoter,
    }
    processed_artefacts_status = {}
    processed_artefacts_error_messages = {}
    for family, promoter_function in family_mapping.items():
        artefacts = get_artefacts_by_family(session, family)
        for artefact in artefacts:
            artefact_key = f"{family} - {artefact.name} - {artefact.version}"
            try:
                processed_artefacts_status[artefact_key] = True
                promoter_function(session, artefact)
            except Exception as exc:
                processed_artefacts_status[artefact_key] = False
                processed_artefacts_error_messages[artefact_key] = str(exc)
                logger.warning("WARNING: %s", str(exc), exc_info=True)
    return processed_artefacts_status, processed_artefacts_error_messages


def run_snap_promoter(db_session: Session, snap: Artefact):
    assert snap.family == FamilyName.snap
    assert snap.store, f"Store is not set for the snap artefact {snap.id}"

    all_channel_maps = get_channel_map_from_snapcraft(
        snapstore=snap.store,
        snap_name=snap.name,
    )
    snap.stage = max(
        (
            cm.channel.risk
            for cm in all_channel_maps
            if cm.channel.track == snap.track
            and cm.channel.architecture in snap.architectures
            and cm.version == snap.version
        ),
        default=snap.stage,
    )
    db_session.commit()


def run_deb_promoter(session: Session, artefact: Artefact) -> None:
    """
    Check deb artefacts state and move/archive them if necessary

    :session: DB connection session
    :artefact: an Artefact object
    """
    series = artefact.series
    repo = artefact.repo
    assert series is not None, f"Series is not set for the artefact {artefact.id}"
    assert repo is not None, f"Repo is not set for the artefact {artefact.id}"

    for arch in artefact.architectures:
        for pocket in POCKET_PROMOTION_MAP:
            with ArchiveManager(
                arch=arch,
                series=series,
                pocket=pocket,
                apt_repo=repo,
            ) as archivemanager:
                deb_version = archivemanager.get_deb_version(artefact.name)
                if deb_version is None:
                    logger.error(
                        "Cannot find deb_version with deb %s in package data",
                        artefact.name,
                    )
                    continue
            next_pocket = POCKET_PROMOTION_MAP.get(artefact.stage)
            logger.debug(
                "Artefact version: %s, deb version: %s", artefact.version, deb_version
            )
            if (
                next_pocket
                and pocket == next_pocket != artefact.stage
                and deb_version == artefact.version
            ):
                logger.info(
                    "Move artefact '%s' to the '%s' stage", artefact, next_pocket
                )
                artefact.stage = next_pocket
                session.commit()
