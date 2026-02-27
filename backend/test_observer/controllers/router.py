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

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from test_observer.controllers.applications import applications
from test_observer.controllers.docs import docs
from test_observer.controllers.permissions import permissions
from test_observer.controllers.users import users
from test_observer.data_access.setup import get_db

from . import (
    auth,
    environments,
    reports,
    test_cases,
    test_executions,
    test_results,
)
from .application import version
from .artefacts import artefacts
from .execution_metadata import execution_metadata
from .issues import issues
from .teams import teams
from .test_executions import relevant_links

router: APIRouter = APIRouter()
router.include_router(version.router, prefix="/v1/version")
router.include_router(test_executions.router, prefix="/v1/test-executions")
router.include_router(artefacts.router, prefix="/v1/artefacts")
router.include_router(reports.router, prefix="/v1/reports")
router.include_router(test_cases.router, prefix="/v1/test-cases")
router.include_router(environments.router, prefix="/v1/environments")
router.include_router(relevant_links.router, prefix="/v1/test-executions")
router.include_router(issues.router, prefix="/v1/issues")
router.include_router(test_results.router, prefix="/v1/test-results")
router.include_router(execution_metadata.router, prefix="/v1/execution-metadata")
router.include_router(auth.router, prefix="/v1/auth")
router.include_router(users.router, prefix="/v1/users")
router.include_router(teams.router, prefix="/v1/teams")
router.include_router(permissions.router, prefix="/v1/permissions")
router.include_router(applications.router, prefix="/v1/applications")
router.include_router(docs.router)


@router.get("/")
def root(db: Session = Depends(get_db)):
    db.execute(text("select 'test db connection'"))
    return "test observer api"


@router.get("/sentry-debug")
def trigger_error():
    division_by_zero = 1 / 0
    return division_by_zero
