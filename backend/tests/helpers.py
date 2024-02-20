from datetime import datetime

from sqlalchemy.orm import Session

from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    Stage,
    TestCase,
    TestExecution,
    TestResult,
)
from test_observer.data_access.models_enums import (
    FamilyName,
    TestExecutionReviewDecision,
    TestExecutionStatus,
    TestResultStatus,
)

DEFAULT_ARCHITECTURE = "amd64"


def create_artefact(db_session: Session, stage_name: str, **kwargs) -> Artefact:
    """Create a dummy artefact"""
    stage = db_session.query(Stage).filter(Stage.name == stage_name).one()
    family = FamilyName(stage.family.name)

    artefact = Artefact(
        name=kwargs.get("name", ""),
        stage=stage,
        version=kwargs.get("version", "1.1.1"),
        track=kwargs.get("track", "latest" if family == FamilyName.SNAP else None),
        store=kwargs.get("store", "ubuntu" if family == FamilyName.SNAP else None),
        series=kwargs.get("series", "jammy" if family == FamilyName.DEB else None),
        repo=kwargs.get("repo", "main" if family == FamilyName.DEB else None),
        created_at=kwargs.get("created_at", datetime.utcnow()),
        status=kwargs.get("status"),
    )
    db_session.add(artefact)
    db_session.commit()
    return artefact


def create_artefact_build(
    db_session: Session,
    artefact: Artefact,
    architecture: str = DEFAULT_ARCHITECTURE,
    revision: int | None = None,
) -> ArtefactBuild:
    if artefact.stage.family == FamilyName.SNAP:
        revision = 1

    build = ArtefactBuild(
        architecture=architecture,
        revision=revision,
        artefact=artefact,
    )
    db_session.add(build)
    db_session.commit()
    return build


def create_environment(
    db_session: Session,
    name: str = "laptop",
    architecture: str = DEFAULT_ARCHITECTURE,
) -> Environment:
    environment = Environment(name=name, architecture=architecture)
    db_session.add(environment)
    db_session.commit()
    return environment


def create_test_execution(
    db_session: Session,
    artefact_build: ArtefactBuild,
    environment: Environment,
    ci_link: str | None = None,
    c3_link: str | None = None,
    status: TestExecutionStatus = TestExecutionStatus.NOT_STARTED,
    review_decision: list[TestExecutionReviewDecision] | None = None,
    review_comment: str = "",
) -> TestExecution:
    if review_decision is None:
        review_decision = []

    test_execution = TestExecution(
        artefact_build=artefact_build,
        environment=environment,
        ci_link=ci_link,
        c3_link=c3_link,
        status=status,
        review_decision=review_decision,
        review_comment=review_comment,
    )
    db_session.add(test_execution)
    db_session.commit()
    return test_execution


def create_test_case(
    db_session: Session,
    name: str = "camera/detect",
    category: str = "camera",
) -> TestCase:
    test_case = TestCase(name=name, category=category)
    db_session.add(test_case)
    db_session.commit()
    return test_case


def create_test_result(
    db_session: Session,
    test_case: TestCase,
    test_execution: TestExecution,
    status: TestResultStatus = TestResultStatus.PASSED,
    comment: str = "",
    io_log: str = "",
) -> TestResult:
    test_result = TestResult(
        test_case=test_case,
        test_execution=test_execution,
        status=status,
        comment=comment,
        io_log=io_log,
    )
    db_session.add(test_result)
    db_session.commit()
    return test_result
