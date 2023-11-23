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
#        Omar Selo <omar.selo@canonical.com>
#        Nadzeya Hutsko <nadzeya.hutsko@canonical.com>

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from test_observer.data_access.models import Artefact
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.repository import get_artefacts_by_family
from test_observer.data_access.setup import get_db, get_redis
from test_observer.external_apis.c3.c3 import C3Api

from .logic import (
    _parse_status_id_from_c3_link,
    construct_dto_builds,
    get_builds_from_db,
    get_historic_test_executions_from_db,
    get_reports_ids,
    get_statuses_ids,
    get_test_execution_by_environment_id_mapping,
)
from .models import ArtefactBuildDTO, ArtefactDTO

router = APIRouter()


@router.get("", response_model=list[ArtefactDTO])
def get_artefacts(
    family: FamilyName | None = None,
    db: Session = Depends(get_db),
):
    """Get latest artefacts optionally by family"""
    artefacts = []

    if family:
        artefacts = get_artefacts_by_family(db, family, load_stage=True)
    else:
        for family in FamilyName:
            artefacts += get_artefacts_by_family(db, family, load_stage=True)

    return artefacts


@router.get("/{artefact_id}", response_model=ArtefactDTO)
def get_artefact(artefact_id: int, db: Session = Depends(get_db)):
    """Get an artefact by id"""
    artefact = db.get(Artefact, artefact_id)

    if artefact is None:
        raise HTTPException(status_code=404, detail="Artefact not found")

    return artefact


@router.get("/{artefact_id}/builds", response_model=list[ArtefactBuildDTO])
def get_artefact_builds(
    artefact_id: int,
    c3api: Annotated[C3Api, Depends()],
    db: Session = Depends(get_db),
):
    """Get latest artefact builds of an artefact together with their test executions"""
    builds = get_builds_from_db(artefact_id, db)

    test_execution_environments = [
        test_execution.environment_id
        for build in builds
        for test_execution in build.test_executions
        if test_execution.c3_link
    ]

    historic_test_executions = get_historic_test_executions_from_db(
        artefact_id, test_execution_environments, db
    )

    test_executions_by_env_id = get_test_execution_by_environment_id_mapping(
        historic_test_executions
    )

    submissions_statuses = c3api.get_submissions_statuses(
        get_statuses_ids(builds, historic_test_executions)
    )

    reports = c3api.get_reports(get_reports_ids(submissions_statuses.values()))

    dto_builds = construct_dto_builds(
        builds, submissions_statuses, reports, test_executions_by_env_id
    )

    return list(dto_builds)
