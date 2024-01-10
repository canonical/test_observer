from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.query import RowReturningQuery

from test_observer.common.constants import HISTORIC_TEST_RESULT_COUNT
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    TestCase,
    TestExecution,
    TestResult,
)
from test_observer.data_access.models_enums import TestExecutionStatus, TestResultStatus
from test_observer.data_access.repository import get_or_create

from .models import C3TestResult, C3TestResultStatus


def compute_test_execution_status(
    test_results: list[TestResult],
) -> TestExecutionStatus:
    failed = any(r.status == TestResultStatus.FAILED for r in test_results)
    status = TestExecutionStatus.FAILED if failed else TestExecutionStatus.PASSED
    return status


def store_test_results(
    db: Session,
    c3_test_results: list[C3TestResult],
    test_execution: TestExecution,
):
    for r in c3_test_results:
        test_case = get_or_create(
            db,
            TestCase,
            filter_kwargs={"name": r.name},
            creation_kwargs={"category": r.category},
        )

        test_result = TestResult(
            test_case=test_case,
            test_execution=test_execution,
            status=parse_c3_test_result_status(r.status),
            comment=r.comment,
            io_log=r.io_log,
        )

        db.add(test_result)

    db.commit()


def parse_c3_test_result_status(status: C3TestResultStatus) -> TestResultStatus:
    match status:
        case C3TestResultStatus.PASS:
            return TestResultStatus.PASSED
        case C3TestResultStatus.FAIL:
            return TestResultStatus.FAILED
        case C3TestResultStatus.SKIP:
            return TestResultStatus.SKIPPED


def get_historic_artefact_builds_query(
    session: Session,
    artefact: Artefact,
    architecture: str,
) -> RowReturningQuery:
    """
    Helper method to get a query that fetches the latest Artefact Build IDs
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


def get_historic_test_executions_query(
    session: Session,
    test_execution: TestExecution,
    artefact_build_query: RowReturningQuery,
) -> RowReturningQuery:
    """
    Helper method to get a query that fetches the latest Test Execution IDs
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
        .limit(HISTORIC_TEST_RESULT_COUNT)
    )


def get_historic_test_results(
    session: Session,
    test_execution: TestExecution,
) -> list[TestResult]:
    """
    Helper method to get the historic test results (10 latest) for
    a given Test Execution object

    Parameters:
        session (Session): Database session object used to generate the query for
        test_execution (TestExecution): TestExecution object to filter based on

    Returns:
        List of Test Result objects that match the test execution objects
        received as input
    """

    artefact_builds_query = get_historic_artefact_builds_query(
        session=session,
        artefact=test_execution.artefact_build.artefact,
        architecture=test_execution.artefact_build.architecture,
    )
    test_executions_query = get_historic_test_executions_query(
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
