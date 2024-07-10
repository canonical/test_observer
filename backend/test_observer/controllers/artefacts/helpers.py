from sqlalchemy import Subquery, func
from sqlalchemy.orm import Session

from test_observer.controllers.artefacts.models import ArtefactDTO
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    TestExecution,
)


def _get_test_execution_counts_subquery(db: Session) -> Subquery:
    """
    Helper method to get a subquery that fetches the counts of both:
    * total Test Executions related to the Artefact
    * completed Test Executions related to the Artefact

    Completed Test Execution is defined as one having at least one
    review decision

    Parameters:
        db (Session): Database session object used to generate the query for

    Returns:
        Subquery SQLAlchemy object to be used in the main query, where we can
        merge Artefacts queries with other filters with the counts fetched
        from this helper method
    """
    # Define subquery to count all TestExecutions for each Artefact
    all_tests = (
        db.query(
            ArtefactBuild.artefact_id,
            func.count(TestExecution.id).label("total"),
        )
        .join(TestExecution, TestExecution.artefact_build_id == ArtefactBuild.id)
        .group_by(ArtefactBuild.artefact_id)
        .subquery()
    )

    # Define subquery to count completed TestExecutions for each Artefact
    completed_tests = (
        db.query(
            ArtefactBuild.artefact_id,
            func.count(TestExecution.id).label("completed"),
        )
        .join(TestExecution, TestExecution.artefact_build_id == ArtefactBuild.id)
        .filter(func.array_length(TestExecution.review_decision, 1) > 0)
        .group_by(ArtefactBuild.artefact_id)
        .subquery()
    )

    # Define the query to merge subquery for all and completed test executions
    return (
        db.query(
            all_tests.c.artefact_id,
            func.coalesce(all_tests.c.total, 0).label("total"),
            func.coalesce(completed_tests.c.completed, 0).label("completed"),
        )
        .outerjoin(
            completed_tests, all_tests.c.artefact_id == completed_tests.c.artefact_id
        )
        .subquery()
    )


def _get_test_executions_count_dict(
    db: Session, artefact_ids: list[int]
) -> dict[int, dict[str, int]]:
    """
    Helper method to fetch the counts for all/completed test executions
    related to an artefact and return them as a dictionary where the key is
    the artefact id

    Parameters:
        db (Session): Database session object used to generate the query for
        artefact_ids (list[int]): List of Artefact IDs to fetch the counts for
    Returns:
        Dictionary where the key is the Artefact ID and the value is a dictionary
        with the counts of all and completed test executions
    """
    test_execution_counts = _get_test_execution_counts_subquery(db)

    # Execute the query and fetch all results
    results = (
        db.query(
            Artefact.id,
            func.coalesce(test_execution_counts.c.total, 0).label("total"),
            func.coalesce(test_execution_counts.c.completed, 0).label("completed"),
        )
        .outerjoin(
            test_execution_counts, Artefact.id == test_execution_counts.c.artefact_id
        )
        .filter(Artefact.id.in_(artefact_ids))
        .all()
    )

    # Convert the results to a dictionary
    return {
        artefact_id: {
            "total": total,
            "completed": completed,
        }
        for artefact_id, total, completed in results
    }


def parse_artefact_orm_object(
    artefact: Artefact, counts_dict: dict[int, dict[str, int]]
) -> ArtefactDTO:
    """
    Parses the Artefact ORM object to a DTO object and adds the counts of
    all and completed test executions to the DTO object

    Parameters:
        artefact (Artefact): Artefact ORM object to parse
        counts_dict (dict[int, dict[str, int]]): Dictionary with the counts of
        all and completed test executions for each Artefact ID
    Returns:
        ArtefactDTO object with the counts of all and completed test executions
        added to the object
    """
    parsed_artefact = ArtefactDTO.model_validate(artefact)
    if counts_dict.get(artefact.id):
        parsed_artefact.all_test_executions_count = counts_dict[artefact.id].get(
            "total", 0
        )
        parsed_artefact.completed_test_executions_count = counts_dict[artefact.id].get(
            "completed", 0
        )
    return parsed_artefact
