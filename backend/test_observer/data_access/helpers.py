from sqlalchemy.orm import Session

from test_observer.data_access.models import Artefact, ArtefactBuild, TestExecution

HISTORIC_TEST_RESULT_COUNT = 10


def _get_historic_test_executions_ids(
    session: Session,
    test_execution: TestExecution,
) -> list[int]:
    current_artefact = test_execution.artefact_build.artefact
    historic_test_execution_ids = (
        session.query(TestExecution.id)
        .join(ArtefactBuild, TestExecution.artefact_build_id == ArtefactBuild.id)
        .join(Artefact, ArtefactBuild.artefact_id == Artefact.id)
        .filter(
            Artefact.name == current_artefact.name,
            Artefact.store == current_artefact.store,
            Artefact.repo == current_artefact.repo,
            Artefact.series == current_artefact.series,
            TestExecution.environment_id == test_execution.environment_id,
            TestExecution.id < test_execution.id,
        )
        .order_by(TestExecution.created_at.desc())
        .limit(HISTORIC_TEST_RESULT_COUNT)
        .all()
    )

    return [id[0] for id in historic_test_execution_ids]
