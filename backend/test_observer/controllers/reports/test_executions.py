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
from pathlib import Path

from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy import Select, func, select, text
from sqlalchemy.orm import Session

from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    ArtefactBuildEnvironmentReview,
    Environment,
    TestEvent,
    TestExecution,
)
from test_observer.data_access.setup import get_db

router = APIRouter()

TEST_EXECUTIONS_REPORT_COLUMNS = [
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
    TestExecution.id,
    TestExecution.status,
    TestExecution.ci_link,
    TestExecution.c3_link,
    TestExecution.checkbox_version,
    TestExecution.test_plan,
    TestExecution.created_at,
    Environment.name,
    Environment.architecture,
    ArtefactBuildEnvironmentReview.review_decision,
    ArtefactBuildEnvironmentReview.review_comment,
    func.coalesce(text("test_executions_events.testevents"), []).label("testevents"),
]

TEST_EXECUTIONS_REPORT_HEADERS = [
    "Artefact.family",
    "Artefact.id",
    "Artefact.name",
    "Artefact.version",
    "Artefact.status",
    "Artefact.track",
    "Artefact.stage",
    "Artefact.series",
    "Artefact.repo",
    "Artefact.os",
    "TestExecution.id",
    "TestExecution.status",
    "TestExecution.ci_link",
    "TestExecution.c3_link",
    "TestExecution.checkbox_version",
    "TestExecution.test_plan",
    "TestExecution.created_at",
    "Environment.name",
    "Environment.architecture",
    "ArtefactBuildEnvironmentReview.review_decision",
    "ArtefactBuildEnvironmentReview.review_comment",
    "TestEvents",
]


def _get_test_executions_reports_query(
    start_date: datetime, end_date: datetime
) -> Select:
    """
    Builds the query that retrieves the test executions based on the parameters set
    """
    test_events_subq = (
        select(
            TestEvent.test_execution_id.label("test_execution_id"),
            func.array_agg(
                func.json_build_object(
                    "event_name",
                    TestEvent.event_name,
                    "timestamp",
                    func.to_char(TestEvent.timestamp, "YYYY-MM-DD HH24:MI:SS:MS"),
                    "detail",
                    TestEvent.detail,
                ),
            ).label("testevents"),
        )
        .where(
            TestExecution.created_at >= start_date, TestExecution.created_at <= end_date
        )
        .join_from(TestEvent, TestExecution)
        .group_by(TestEvent.test_execution_id)
        .alias("test_executions_events")
    )

    return (
        select(
            *TEST_EXECUTIONS_REPORT_COLUMNS,
        )
        .join_from(TestExecution, Environment)
        .join_from(TestExecution, ArtefactBuild)
        .join_from(ArtefactBuild, Artefact)
        .join(
            ArtefactBuildEnvironmentReview,
            (ArtefactBuildEnvironmentReview.artefact_build_id == ArtefactBuild.id)
            & (ArtefactBuildEnvironmentReview.environment_id == Environment.id),
        )
        .join(
            test_events_subq,
            TestExecution.id == test_events_subq.c.test_execution_id,
            isouter=True,
        )
        .where(
            TestExecution.created_at >= start_date, TestExecution.created_at <= end_date
        )
    )


@router.get("/test-executions", response_class=FileResponse)
def get_test_execution_reports(
    background_tasks: BackgroundTasks,
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

    try:
        with open(filename, "w") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(TEST_EXECUTIONS_REPORT_HEADERS)
            writer.writerows(cursor)
    finally:
        # Background tasks get called after the response was returned.
        # So effectively, this will delete the file after it was returned to the user
        background_tasks.add_task(lambda: Path(filename).unlink(missing_ok=True))

    return filename
