# Copyright (C) 2023 Canonical Ltd.
#
# This file is part of Test Observer Backend.
#
# Test Observer Backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# Test Observer Backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import csv
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute

from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    TestCase,
    TestExecution,
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
    Artefact.series,
    Artefact.repo,
    Artefact.os,
    Artefact.series,
    Artefact.created_at,
    TestExecution.id,
    TestExecution.status,
    TestExecution.c3_link,
    TestExecution.checkbox_version,
    TestExecution.test_plan,
    Environment.name,
    Environment.architecture,
    TestCase.template_id,
    TestCase.name,
    TestCase.category,
    TestResult.status,
    TestResult.created_at,
]


@router.get("/test-results", response_class=FileResponse)
def get_testresults_report(
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
        .join_from(TestExecution, TestResult)
        .join_from(TestResult, TestCase)
        .where(Artefact.created_at >= start_date, Artefact.created_at <= end_date)
    )

    filename = "testresults_report.csv"
    with open(filename, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(TESTRESULTS_REPORT_COLUMNS)
        writer.writerows(cursor)

    return filename
