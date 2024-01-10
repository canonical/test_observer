from sqlalchemy.orm import Session

from test_observer.controllers.test_executions.logic import (
    get_historic_artefact_builds_query,
    get_historic_test_executions_query,
)
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    Stage,
    TestExecution,
)


def _get_test_execution(
    db_session: Session, environment: Environment, ci_link: str
) -> TestExecution:
    stage = db_session.query(Stage).filter(Stage.name == "beta").first()
    artefact = Artefact(name="some artefact", version="1.0.0", stage=stage)
    artefact_build = ArtefactBuild(architecture="some arch", artefact=artefact)
    test_execution = TestExecution(
        environment=environment,
        artefact_build=artefact_build,
        ci_link=ci_link,
    )

    db_session.add_all([artefact, artefact_build, test_execution])
    db_session.commit()

    return test_execution


def test_get_historic_artefact_builds_query(db_session: Session):
    stage = db_session.query(Stage).filter(Stage.name == "beta").first()

    artefact_one = Artefact(name="some artefact", version="1.0.0", stage=stage)
    artefact_build_one = ArtefactBuild(architecture="some arch", artefact=artefact_one)

    db_session.add_all([artefact_one, artefact_build_one])
    db_session.commit()

    artefact_two = Artefact(name="some artefact", version="1.0.1", stage=stage)
    artefact_build_two = ArtefactBuild(architecture="some arch", artefact=artefact_two)
    artefact_build_three = ArtefactBuild(
        architecture="another arch", artefact=artefact_two
    )

    db_session.add_all([artefact_two, artefact_build_two, artefact_build_three])
    db_session.commit()

    artefact_builds_query = get_historic_artefact_builds_query(
        session=db_session,
        artefact=artefact_one,
        architecture=artefact_build_two.architecture,
    )

    assert [id[0] for id in artefact_builds_query.all()] == [
        artefact_build_two.id,
        artefact_build_one.id,
    ]


def test_get_historic_artefact_builds_query_returns_latest_revision_build(
    db_session: Session,
):
    stage = db_session.query(Stage).filter(Stage.name == "beta").first()

    artefact_one = Artefact(name="some artefact", version="1.0.0", stage=stage)
    artefact_build_one = ArtefactBuild(
        architecture="some arch", artefact=artefact_one, revision=1
    )
    artefact_build_two = ArtefactBuild(
        architecture="some arch", artefact=artefact_one, revision=2
    )
    artefact_build_three = ArtefactBuild(
        architecture="some arch", artefact=artefact_one, revision=3
    )

    db_session.add_all(
        [artefact_one, artefact_build_one, artefact_build_two, artefact_build_three]
    )
    db_session.commit()

    artefact_builds_query = get_historic_artefact_builds_query(
        session=db_session,
        artefact=artefact_one,
        architecture=artefact_build_two.architecture,
    )

    assert [id[0] for id in artefact_builds_query] == [
        artefact_build_three.id,
    ]


def test_get_historic_test_executions_query(db_session: Session):
    environment_one = Environment(name="some environment", architecture="some arch")
    db_session.add(environment_one)
    db_session.commit()

    test_execution_one = _get_test_execution(
        db_session, environment_one, "https://example1"
    )

    environment_two = Environment(name="another environment", architecture="some arch")
    db_session.add(environment_two)
    db_session.commit()

    test_execution_two = _get_test_execution(
        db_session, environment_two, "https://example2"
    )

    test_execution_three = _get_test_execution(
        db_session, environment_one, "https://example3"
    )

    artefact_build_query = get_historic_artefact_builds_query(
        session=db_session,
        artefact=test_execution_one.artefact_build.artefact,
        architecture=test_execution_one.artefact_build.architecture,
    )

    assert [id[0] for id in artefact_build_query] == [
        test_execution_three.artefact_build_id,
        test_execution_two.artefact_build_id,
        test_execution_one.artefact_build_id,
    ]

    test_execution_ids = get_historic_test_executions_query(
        session=db_session,
        test_execution=test_execution_three,
        artefact_build_query=artefact_build_query,
    )

    assert [id[0] for id in test_execution_ids] == [test_execution_one.id]
