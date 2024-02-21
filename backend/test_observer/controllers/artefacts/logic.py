from itertools import groupby
from operator import attrgetter

from test_observer.data_access.models import Artefact, ArtefactBuild
from test_observer.data_access.models_enums import TestExecutionReviewDecision


def are_all_test_executions_approved(artefact: Artefact) -> bool:
    return all(
        test_execution.review_decision
        and TestExecutionReviewDecision.REJECTED not in test_execution.review_decision
        for build in _artefact_latest_builds(artefact)
        for test_execution in build.test_executions
    )


def is_there_a_rejected_test_execution(artefact: Artefact) -> bool:
    return any(
        TestExecutionReviewDecision.REJECTED in test_execution.review_decision
        for build in _artefact_latest_builds(artefact)
        for test_execution in build.test_executions
    )


def _artefact_latest_builds(artefact: Artefact) -> list[ArtefactBuild]:
    return [
        max(group, key=attrgetter("revision"))
        for _, group in groupby(
            artefact.builds,
            attrgetter("artefact_id", "architecture"),
        )
    ]
