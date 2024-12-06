import csv
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    ArtefactBuildEnvironmentReview,
    Environment,
    Family,
    Stage,
    TestEvent,
    TestExecution,
)
from test_observer.data_access.setup import get_db

router = APIRouter()

TEST_EXECUTIONS_REPORT_COLUMNS = [
    Family.name,
    Artefact.id,
    Artefact.name,
    Artefact.version,
    Artefact.status,
    Artefact.track,
    Artefact.series,
    Artefact.repo,
    TestExecution.id,
    TestExecution.status,
    TestExecution.ci_link,
    TestExecution.c3_link,
    TestExecution.checkbox_version,
    TestExecution.created_at,
    Environment.name,
    Environment.architecture,
    ArtefactBuildEnvironmentReview.review_decision,
    ArtefactBuildEnvironmentReview.review_comment,
]


def _get_test_executions_reports_query(
    start_date: datetime, end_date: datetime
) -> Select:
    """
    Builds the query that retrieves the test executions based on the parameters set
    """
    return (
        select(
            *TEST_EXECUTIONS_REPORT_COLUMNS,
            func.coalesce(
                func.array_agg(
                    func.json_build_object(
                        "event_name",
                        TestEvent.event_name,
                        "timestamp",
                        func.to_char(TestEvent.timestamp, "YYYY-MM-DD HH24:MI:SS:MS"),
                        "detail",
                        TestEvent.detail,
                    )
                )
                .filter(TestEvent.event_name.isnot(None))
                .over(partition_by=TestExecution.id),
                [],
            ).label("test_executions_events.testevents")
        )
        .join_from(TestExecution, TestEvent, isouter=True)
        .join_from(TestExecution, Environment)
        .join_from(TestExecution, ArtefactBuild)
        .join_from(ArtefactBuild, Artefact)
        .join_from(Artefact, Stage)
        .join_from(Stage, Family)
        .join(
            ArtefactBuildEnvironmentReview,
            (ArtefactBuildEnvironmentReview.artefact_build_id == ArtefactBuild.id)
            & (ArtefactBuildEnvironmentReview.environment_id == Environment.id),
        )
        .where(
            TestExecution.created_at >= start_date, TestExecution.created_at <= end_date
        )
    )


@router.get("/test-executions", response_class=FileResponse)
def get_test_execution_reports(
    start_date: datetime = datetime.min,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
):
    """
    Returns a csv report detailing all test executions within a given date range.
    Together with their artefact and environment details in csv format.
    """

    if end_date is None:
        end_date = datetime.now()

    cursor = db.execute(_get_test_executions_reports_query(start_date, end_date))

    filename = "test_executions_report.csv"
    with open(filename, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(TEST_EXECUTIONS_REPORT_COLUMNS)
        writer.writerows(cursor)

    return filename
