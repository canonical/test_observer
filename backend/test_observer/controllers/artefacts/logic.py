from test_observer.data_access.models import ArtefactBuild
from test_observer.data_access.models_enums import TestExecutionReviewDecision


def are_all_test_executions_approved(builds: list[ArtefactBuild]) -> bool:
    return all(
        test_execution.review_decision
        and TestExecutionReviewDecision.REJECTED not in test_execution.review_decision
        for build in builds
        for test_execution in build.test_executions
    )


def is_there_a_rejected_test_execution(builds: list[ArtefactBuild]) -> bool:
    return any(
        TestExecutionReviewDecision.REJECTED in test_execution.review_decision
        for build in builds
        for test_execution in build.test_executions
    )
