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
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from test_observer.data_access.setup import get_db

from .application import version
from .artefacts import artefacts
from .promoter import promoter
from .reports import reports
from .test_executions import test_executions

router = APIRouter()
router.include_router(promoter.router)
router.include_router(version.router, prefix="/v1/version")
router.include_router(test_executions.router, prefix="/v1/test-executions")
router.include_router(artefacts.router, prefix="/v1/artefacts")
router.include_router(reports.router, prefix="/v1/reports")


@router.get("/")
def root(db: Session = Depends(get_db)):
    db.execute(text("select 'test db connection'"))
    return "test observer api"


@router.get("/sentry-debug")
def trigger_error():
    division_by_zero = 1 / 0
    return division_by_zero
