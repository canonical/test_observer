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

import csv
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, Security
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute

from test_observer.common.permissions import Permission, permission_checker
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    TestCase,
    TestExecution,
    TestPlan,
    TestResult,
)
from test_observer.data_access.setup import get_db

router = APIRouter()

TESTRESULTS_REPORT_COLUMNS: list[InstrumentedAttribute] = [
    Artefact.family,
    Artefact.id,
    Artefact.name,
    Artefact.version,
    Artefact.status,
    Artefact.track,
    Artefact.stage,
    Artefact.series,
    Artefact.repo,
    Artefact.os,
    Artefact.series,
    Artefact.created_at,
    TestExecution.id,
    TestExecution.status,
    TestExecution.c3_link,
    TestExecution.checkbox_version,
    TestPlan.name,
    Environment.name,
    Environment.architecture,
    TestCase.template_id,
    TestCase.name,
    TestCase.category,
    TestResult.status,
    TestResult.created_at,
]


@router.get(
    "/test-results",
    response_class=FileResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_report])],
)
def get_testresults_report(
    background_tasks: BackgroundTasks,
    start_date: datetime = datetime.min,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
):
    """
    Returns a csv report detailing all artefacts within a given date range. Together
    with their test executions and test results in csv format.
    """
    if end_date is None:
        end_date = datetime.now()

    cursor = db.execute(
        select(*TESTRESULTS_REPORT_COLUMNS)
        .join_from(Artefact, ArtefactBuild)
        .join_from(ArtefactBuild, TestExecution)
        .join_from(TestExecution, Environment)
        .join_from(TestExecution, TestPlan)
        .join_from(TestExecution, TestResult)
        .join_from(TestResult, TestCase)
        .where(Artefact.created_at >= start_date, Artefact.created_at <= end_date)
    )

    filename = "testresults_report.csv"

    try:
        with open(filename, "w") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(TESTRESULTS_REPORT_COLUMNS)
            writer.writerows(cursor)
    finally:
        # Background tasks get called after the response was returned.
        # So effectively, this will delete the file after it was returned to the user
        background_tasks.add_task(lambda: Path(filename).unlink(missing_ok=True))

    return filename
