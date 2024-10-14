from test_observer.data_access.models import ArtefactBuild
from test_observer.data_access.models_enums import (
    ArtefactBuildEnvironmentReviewDecision,
)


def are_all_environments_approved(builds: list[ArtefactBuild]) -> bool:
    return all(
        review.review_decision
        and ArtefactBuildEnvironmentReviewDecision.REJECTED
        not in review.review_decision
        for build in builds
        for review in build.environment_reviews
    )


def is_there_a_rejected_environment(builds: list[ArtefactBuild]) -> bool:
    return any(
        ArtefactBuildEnvironmentReviewDecision.REJECTED in review.review_decision
        for build in builds
        for review in build.environment_reviews
    )
