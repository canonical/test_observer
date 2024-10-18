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

from sqlalchemy import delete, desc
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.query import RowReturningQuery

from test_observer.common.constants import PREVIOUS_TEST_RESULT_COUNT
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    TestEvent,
    TestExecution,
    TestExecutionRerunRequest,
    TestResult,
)
from test_observer.data_access.models_enums import TestExecutionStatus

from .models import StartTestExecutionRequest


def reset_test_execution(
    request: StartTestExecutionRequest,
    db: Session,
    test_execution: TestExecution,
):
    test_execution.status = TestExecutionStatus.IN_PROGRESS
    test_execution.ci_link = request.ci_link
    test_execution.c3_link = None
    db.commit()


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


def get_previous_artefact_builds_query(
    session: Session,
    artefact: Artefact,
    architecture: str,
) -> RowReturningQuery:
    """
    Helper method to get a query that fetches the previous Artefact Build IDs
    for given Artefact object identifiers (name, track, repo, store) and architecture.

    The query only returns the latest revision build for each Artefact, in case there
    are multiple revision of the same artefact version.

    Parameters:
        session (Session): Database session object used to generate the query for
        artefact (Artefact): Artefact objects used to take the identifiers from
        architecture (str): Architecture name to filter the results returned

    Returns:
        Prepared query object that can be executed as a query itself using .all()
        or a subquery using .subquery()
    """

    return (
        session.query(ArtefactBuild.id)
        .distinct(ArtefactBuild.artefact_id)
        .join(ArtefactBuild.artefact)
        .filter(
            Artefact.name == artefact.name,
            Artefact.track == artefact.track,
            Artefact.repo == artefact.repo,
            Artefact.series == artefact.series,
            ArtefactBuild.architecture == architecture,
        )
        .order_by(
            desc(ArtefactBuild.artefact_id),
            desc(ArtefactBuild.revision),
        )
    )


def get_previous_test_executions_query(
    session: Session,
    test_execution: TestExecution,
    artefact_build_query: RowReturningQuery,
) -> RowReturningQuery:
    """
    Helper method to get a query that fetches the previous Test Execution IDs
    for all test executions that come from the artefact_build_ids subquery.

    The query returns only the test executions that belong to the same environment
    as the given input test execution

    Parameters:
        session (Session): Database session object used to generate the query for
        test_execution (TestExecution): TestExecution object to filter based on
        artefact_build_query (RowReturningQuery): Query to fetch the artefact builds

    Returns:
        Prepared query object that can be executed as a query itself using .all()
        or a subquery using .subquery()
    """

    return (
        session.query(TestExecution.id)
        .filter(
            TestExecution.artefact_build_id.in_(artefact_build_query.scalar_subquery()),
            TestExecution.environment_id == test_execution.environment_id,
            TestExecution.id < test_execution.id,
        )
        .order_by(desc(TestExecution.id))
        .limit(PREVIOUS_TEST_RESULT_COUNT)
    )


def get_previous_test_results(
    session: Session,
    test_execution: TestExecution,
) -> list[TestResult]:
    """
    Helper method to get the previous test results (10 latest) for
    a given Test Execution object

    Parameters:
        session (Session): Database session object used to generate the query for
        test_execution (TestExecution): TestExecution object to filter based on

    Returns:
        List of Test Result objects that match the test execution objects
        received as input
    """

    artefact_builds_query = get_previous_artefact_builds_query(
        session=session,
        artefact=test_execution.artefact_build.artefact,
        architecture=test_execution.artefact_build.architecture,
    )
    test_executions_query = get_previous_test_executions_query(
        session=session,
        test_execution=test_execution,
        artefact_build_query=artefact_builds_query,
    )

    # It is important to have the order_by(TestResult.test_case_id) in this query
    # This is because we use the output of this function with itertools.groupby
    # which merges consecutive items by key, and needs the items sorted to group
    # everything correctly
    return (
        session.query(TestResult)
        .options(
            joinedload(TestResult.test_execution)
            .joinedload(TestExecution.artefact_build)
            .joinedload(ArtefactBuild.artefact)
        )
        .filter(
            TestResult.test_execution_id.in_(test_executions_query.scalar_subquery())
        )
        .order_by(TestResult.test_case_id, desc(TestResult.id))
        .all()
    )


def delete_rerun_request(db: Session, test_execution_id: int):
    db.execute(
        delete(TestExecutionRerunRequest).where(
            TestExecutionRerunRequest.test_execution_id == test_execution_id
        )
    )
    db.commit()
