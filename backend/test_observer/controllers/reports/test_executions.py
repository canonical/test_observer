import csv
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy import select, func, Select
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.engine import Result
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute

from test_observer.data_access import queries
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuildEnvironmentReview,
    Environment,
    Family,
    Stage,
    TestCase,
    TestEvent,
    TestExecution,
    TestResult,
)
from test_observer.data_access.setup import get_db


router = APIRouter()


TEST_EXECUTIONS_REPORT_COLUMNS: list[Any] = [
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
    TestExecution.ci_link,
    TestExecution.c3_link,
    TestExecution.checkbox_version,
    Environment.name,
    Environment.architecture,
    ArtefactBuildEnvironmentReview.review_decision,
    ArtefactBuildEnvironmentReview.review_comment,
]


def _get_test_execution_reports_query(
    columns: list[InstrumentedAttribute],
    include_test_events: bool,
    start_date: datetime,
    end_date: datetime,
) -> Select:
    """
    Builds the query that retrieves the test executions based on the parameters set
    """
    latest_builds = queries.latest_artefact_builds.subquery()
    base_query = (
        select(*columns)
        .join_from(TestExecution, Environment)
        .join_from(TestExecution, latest_builds)
        .join_from(latest_builds, Artefact)
        .join_from(Artefact, Stage)
        .join_from(Stage, Family)
        .join(
            ArtefactBuildEnvironmentReview,
            (ArtefactBuildEnvironmentReview.artefact_build_id == latest_builds.c.id)
            & (ArtefactBuildEnvironmentReview.environment_id == Environment.id),
        )
        .where(
            TestExecution.created_at >= start_date, TestExecution.created_at <= end_date
        )
    )

    if include_test_events:
        return base_query.outerjoin(
            TestEvent, TestExecution.id == TestEvent.test_execution_id
        ).group_by(*TEST_EXECUTIONS_REPORT_COLUMNS)

    return base_query


@router.get("/test-executions", response_class=FileResponse)
def get_test_execution_reports(
    start_date: datetime = datetime.min,
    end_date: datetime | None = None,
    include_test_events: bool = False,
    db: Session = Depends(get_db),
):
    """
    Returns a csv report detailing all test executions within a given date range.
    Together with their artefact and environment details in csv format.
    """

    if end_date is None:
        end_date = datetime.now()

    columns = [*TEST_EXECUTIONS_REPORT_COLUMNS]
    column_names = [str(column) for column in TEST_EXECUTIONS_REPORT_COLUMNS]
    if include_test_events:
        columns.extend(
            [
                func.array_agg(
                    aggregate_order_by(TestEvent.event_name, TestEvent.timestamp)
                ),
                func.array_agg(
                    aggregate_order_by(
                        func.to_char(TestEvent.timestamp, "YYYY-MM-DD HH24:MI:SS:MS"),
                        TestEvent.timestamp,
                    ),
                ),
                func.array_agg(
                    aggregate_order_by(TestEvent.detail, TestEvent.timestamp)
                ),
            ]
        )
        column_names.extend(
            ["TestEvent.event_name", "TestEvent.timestamp", "TestEvent.detail"]
        )

    cursor = db.execute(
        _get_test_execution_reports_query(
            columns, include_test_events, start_date, end_date
        )
    )

    filename = "test_executions_report.csv"
    with open(filename, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(column_names)
        writer.writerows(cursor)

    return filename
