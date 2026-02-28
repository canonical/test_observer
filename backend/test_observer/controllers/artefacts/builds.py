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

from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import selectinload

from test_observer.common.permissions import Permission, permission_checker
from test_observer.controllers.artefacts.artefact_retriever import ArtefactRetriever
from test_observer.controllers.test_executions.test_execution import (
    TEST_EXECUTION_OPTIONS,
)
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
)

from .models import (
    ArtefactBuildResponse,
)

router = APIRouter(tags=["artefact-builds"])


@router.get(
    "/{artefact_id}/builds",
    response_model=list[ArtefactBuildResponse],
    dependencies=[Security(permission_checker, scopes=[Permission.view_artefact])],
)
def get_artefact_builds(
    artefact: Artefact = Depends(
        ArtefactRetriever(
            selectinload(Artefact.builds).selectinload(ArtefactBuild.test_executions).options(*TEST_EXECUTION_OPTIONS)
        )
    ),
):
    """Get latest artefact builds of an artefact together with their test executions"""
    for artefact_build in artefact.latest_builds:
        artefact_build.test_executions.sort(key=lambda test_execution: test_execution.environment.name)

    return artefact.latest_builds
