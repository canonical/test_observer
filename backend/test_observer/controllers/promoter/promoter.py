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
#        Omar Selo <omar.selo@canonical.com>


import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from test_observer.data_access.models import Artefact
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.repository import (
    get_artefacts_by_family,
    get_stage_by_name,
)
from test_observer.data_access.setup import get_db
from test_observer.external_apis.archive import ArchiveManager
from test_observer.external_apis.snapcraft import (
    get_channel_map_from_snapcraft,
)

router = APIRouter()

logger = logging.getLogger("test-observer-backend")

CHANNEL_PROMOTION_MAP = {
    # channel -> next-channel
    "edge": "beta",
    "beta": "candidate",
    "candidate": "stable",
    "stable": "stable",
}

POCKET_PROMOTION_MAP = {
    # pocket -> next-pocket
    "proposed": "updates",
    "updates": "updates",
}


@router.put("/v0/artefacts/promote")
def promote_artefacts(db: Session = Depends(get_db)):
    """
    Promote all the artefacts in all the families if it has been updated on the
    external source
    """
    try:
        processed_artefacts = promoter_controller(db)
        logger.info("INFO: Processed artefacts %s", processed_artefacts)
        if False in processed_artefacts.values():
            return JSONResponse(
                status_code=500,
                content={
                    "detail": (
                        "Got some errors while processing the next artefacts: "
                        ", ".join(
                            [k for k, v in processed_artefacts.items() if v is False]
                        )
                    )
                },
            )
        return JSONResponse(
            status_code=200,
            content={"detail": "All the artefacts have been processed successfully"},
        )
    except Exception as exc:
        return JSONResponse(status_code=500, content={"detail": str(exc)})


def promoter_controller(session: Session) -> dict:
    """
    Orchestrate the snap promoter job

    :session: DB connection session
    :return: dict with the processed cards and the status of execution
    """
    family_mapping = {
        FamilyName.SNAP: run_snap_promoter,
        FamilyName.DEB: run_deb_promoter,
    }
    for family_name, promoter_function in family_mapping.items():
        artefacts = get_artefacts_by_family(session, family_name, load_stage=True)
        processed_artefacts = {}
        for artefact in artefacts:
            try:
                processed_artefacts[
                    f"{family_name} - {artefact.name} - {artefact.version}"
                ] = True
                promoter_function(session, artefact)
            except Exception as exc:
                processed_artefacts[
                    f"{family_name} - {artefact.name} - {artefact.version}"
                ] = False
                logger.warning("WARNING: %s", str(exc), exc_info=True)
    return processed_artefacts


def run_snap_promoter(session: Session, artefact: Artefact) -> None:
    """
    Check snap artefacts state and move/archive them if necessary

    :session: DB connection session
    :artefact_build: an ArtefactBuild object
    """
    store = artefact.store
    assert store is not None, f"Store is not set for the artefact {artefact.id}"

    for build in artefact.builds:
        arch = build.architecture
        channel_map = get_channel_map_from_snapcraft(
            arch=arch,
            snapstore=store,
            snap_name=artefact.name,
        )
        track = artefact.track

        for channel_info in channel_map:
            if not (
                channel_info.channel.track == track
                and channel_info.channel.architecture == arch
            ):
                continue

            risk = channel_info.channel.risk
            try:
                version = channel_info.version
                revision = channel_info.revision
            except KeyError as exc:
                logger.warning(
                    "No key '%s' is found. Continue processing...",
                    str(exc),
                )
                continue

            next_risk = CHANNEL_PROMOTION_MAP[artefact.stage.name]
            if (
                risk == next_risk != artefact.stage.name.lower()
                and version == artefact.version
                and revision == build.revision
            ):
                logger.info("Move artefact '%s' to the '%s' stage", artefact, next_risk)
                stage = get_stage_by_name(
                    session, stage_name=next_risk, family=artefact.stage.family
                )
                if stage:
                    artefact.stage = stage
                    session.commit()
                    # The artefact was promoted, so we're done
                    return


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

    for build in artefact.builds:
        arch = build.architecture
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
            next_pocket = POCKET_PROMOTION_MAP.get(artefact.stage.name)
            logger.debug(
                "Artefact version: %s, deb version: %s", artefact.version, deb_version
            )
            if (
                pocket == next_pocket != artefact.stage.name
                and deb_version == artefact.version
            ):
                logger.info(
                    "Move artefact '%s' to the '%s' stage", artefact, next_pocket
                )
                stage = get_stage_by_name(
                    session, stage_name=next_pocket, family=artefact.stage.family
                )
                if stage:
                    artefact.stage = stage
                    session.commit()
                    # The artefact was promoted, so we're done
                    return
