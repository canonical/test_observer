import csv
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute

from test_observer.data_access import queries
from test_observer.data_access.models import (
    Artefact,
    Environment,
    Family,
    Stage,
    TestCase,
    TestExecution,
    TestResult,
)
from test_observer.data_access.setup import get_db

router = APIRouter()

TESTRESULTS_REPORT_COLUMNS: list[InstrumentedAttribute] = [
    Family.name,
    Artefact.id,
    Artefact.name,
    Artefact.version,
    Artefact.status,
    Artefact.track,
    Artefact.series,
    Artefact.repo,
    Artefact.created_at,
    TestExecution.id,
    TestExecution.status,
    TestExecution.review_decision,
    TestExecution.review_comment,
    Environment.name,
    Environment.architecture,
    TestCase.template_id,
    TestCase.name,
    TestCase.category,
    TestResult.status,
    TestResult.created_at,
]


@router.get("/testresults", response_class=FileResponse)
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

    latest_builds = queries.latest_artefact_builds.subquery()

    cursor = db.execute(
        select(*TESTRESULTS_REPORT_COLUMNS)
        .join_from(Family, Stage)
        .join_from(Stage, Artefact)
        .join_from(Artefact, latest_builds)
        .join_from(latest_builds, TestExecution)
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
