# Copyright 2024 Canonical Ltd.
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

from collections import defaultdict

from sqlalchemy import delete, desc, func, or_, over, select
from sqlalchemy.orm import Session

from test_observer.common.constants import PREVIOUS_TEST_RESULT_COUNT
from test_observer.controllers.test_executions.models import PreviousTestResult
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    TestEvent,
    TestExecution,
    TestResult,
)


def delete_previous_results(
    db: Session,
    test_execution: TestExecution,
):
    db.execute(
        delete(TestResult).where(TestResult.test_execution_id == test_execution.id)
    )
    db.commit()


def delete_previous_test_events(
    db: Session,
    test_execution: TestExecution,
):
    db.execute(
        delete(TestEvent).where(TestEvent.test_execution_id == test_execution.id)
    )
    db.commit()


def get_previous_test_results(
    session: Session,
    test_execution: TestExecution,
) -> dict[int, list[PreviousTestResult]]:
    """
    Helper method to get the previous test results up to a maximum for
    all the test cases of a given Test Execution object

    Parameters:
        session (Session): Database session object used to generate the query for
        test_execution (TestExecution): TestExecution object to filter based on

    Returns:
        A dictionary whose key is a test case id and value is an ordered list
        of previous test results from most recent to oldest.
    """

    subq = (
        select(
            TestResult.id.label("result_id"),
            TestResult.status.label("result_status"),
            TestResult.test_case_id.label("case_id"),
            Artefact.id.label("artefact_id"),
            Artefact.version.label("artefact_version"),
            over(
                func.row_number(),
                partition_by=TestResult.test_case_id,
                order_by=[desc(Artefact.id), desc(TestResult.id)],
            ).label("row_number"),
        )
        .join(TestResult.test_execution)
        .join(TestExecution.artefact_build)
        .join(ArtefactBuild.artefact)
        .where(
            TestExecution.environment_id == test_execution.environment_id,
            ArtefactBuild.architecture == test_execution.artefact_build.architecture,
            Artefact.name == test_execution.artefact_build.artefact.name,
            Artefact.series == test_execution.artefact_build.artefact.series,
            Artefact.repo == test_execution.artefact_build.artefact.repo,
            Artefact.track == test_execution.artefact_build.artefact.track,
            Artefact.os == test_execution.artefact_build.artefact.os,
            Artefact.series == test_execution.artefact_build.artefact.series,
            Artefact.id <= test_execution.artefact_build.artefact_id,
            or_(
                TestExecution.id < test_execution.id,
                Artefact.id < test_execution.artefact_build.artefact_id,
            ),
        )
    ).subquery()

    stmt = (
        select(
            subq.c.case_id,
            subq.c.result_status,
            subq.c.artefact_id,
            subq.c.artefact_version,
        )
        .where(subq.c.row_number <= PREVIOUS_TEST_RESULT_COUNT)
        .order_by(
            subq.c.case_id,
            desc(subq.c.artefact_id),
            desc(subq.c.result_id),
        )
    )

    previous_results = defaultdict(list)
    for case_id, result_status, artefact_id, artefact_version in session.execute(stmt):
        previous_results[case_id].append(
            PreviousTestResult(
                status=result_status,
                version=artefact_version,
                artefact_id=artefact_id,
            )
        )

    return previous_results
