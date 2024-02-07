from test_observer.data_access.models import Artefact
from test_observer.data_access.models_enums import TestExecutionReviewDecision


def are_all_test_executions_approved(artefact: Artefact) -> bool:
    return all(
        test_execution.review_decision
        and TestExecutionReviewDecision.REJECTED not in test_execution.review_decision
        for build in artefact.builds
        for test_execution in build.test_executions
    )


def is_there_a_rejected_test_execution(artefact: Artefact) -> bool:
    return any(
        TestExecutionReviewDecision.REJECTED in test_execution.review_decision
        for build in artefact.builds
        for test_execution in build.test_executions
    )
