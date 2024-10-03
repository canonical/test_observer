from datetime import date, datetime

from sqlalchemy.orm import Session

from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    ArtefactBuildEnvironmentReview,
    Environment,
    Stage,
    TestCase,
    TestExecution,
    TestExecutionRerunRequest,
    TestResult,
    User,
)
from test_observer.data_access.models_enums import (
    ArtefactStatus,
    FamilyName,
    TestExecutionReviewDecision,
    TestExecutionStatus,
    TestResultStatus,
)

DEFAULT_ARCHITECTURE = "amd64"


class DataGenerator:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def gen_user(
        self,
        name: str = "John Doe",
        launchpad_handle: str = "jd",
        launchpad_email: str = "john@doe.com",
    ) -> User:
        user = User(
            name=name,
            launchpad_email=launchpad_email,
            launchpad_handle=launchpad_handle,
        )
        self._add_object(user)
        return user

    def gen_artefact(
        self,
        stage_name: str,
        name: str = "core",
        version: str = "1.1.1",
        track: str = "",
        store: str = "",
        series: str = "",
        repo: str = "",
        created_at: datetime | None = None,
        status: ArtefactStatus = ArtefactStatus.UNDECIDED,
        bug_link: str = "",
        due_date: date | None = None,
        assignee_id: int | None = None,
    ) -> Artefact:
        stage = self.db_session.query(Stage).filter(Stage.name == stage_name).one()
        family = FamilyName(stage.family.name)

        if family == FamilyName.SNAP:
            track = track or "latest"
            store = store or "ubuntu"

        if family == FamilyName.DEB:
            series = series or "jammy"
            repo = repo or "main"

        created_at = created_at or datetime.utcnow()

        artefact = Artefact(
            name=name,
            stage=stage,
            version=version,
            track=track,
            store=store,
            series=series,
            repo=repo,
            created_at=created_at,
            status=status,
            bug_link=bug_link,
            due_date=due_date,
            assignee_id=assignee_id,
        )
        self._add_object(artefact)
        return artefact

    def gen_artefact_build(
        self,
        artefact: Artefact,
        architecture: str = DEFAULT_ARCHITECTURE,
        revision: int | None = None,
    ) -> ArtefactBuild:
        if revision is None and artefact.stage.family.name == FamilyName.SNAP:
            revision = 1

        build = ArtefactBuild(
            architecture=architecture,
            revision=revision,
            artefact=artefact,
        )
        self._add_object(build)
        return build

    def gen_environment(
        self,
        name: str = "laptop",
        architecture: str = DEFAULT_ARCHITECTURE,
    ) -> Environment:
        environment = Environment(name=name, architecture=architecture)
        self._add_object(environment)
        return environment

    def gen_test_execution(
        self,
        artefact_build: ArtefactBuild,
        environment: Environment,
        ci_link: str | None = None,
        c3_link: str | None = None,
        status: TestExecutionStatus = TestExecutionStatus.NOT_STARTED,
        review_decision: list[TestExecutionReviewDecision] | None = None,
        review_comment: str = "",
        checkbox_version: str | None = None,
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
            checkbox_version=checkbox_version,
        )
        self._add_object(test_execution)
        return test_execution

    def gen_test_case(
        self,
        name: str = "camera/detect",
        category: str = "camera",
        template_id: str = "",
    ) -> TestCase:
        test_case = TestCase(
            name=name,
            category=category,
            template_id=template_id,
        )
        self._add_object(test_case)
        return test_case

    def gen_test_result(
        self,
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
        self._add_object(test_result)
        return test_result

    def gen_rerun_request(
        self, test_execution: TestExecution
    ) -> TestExecutionRerunRequest:
        rerun = TestExecutionRerunRequest(test_execution=test_execution)
        self._add_object(rerun)
        return rerun

    def gen_artefact_build_environment_review(
        self,
        artefact_build_id: int,
        environment_id: int,
        review_decision: list[TestExecutionReviewDecision] | None = None,
        review_comment: str = "",
    ):
        review = ArtefactBuildEnvironmentReview(
            artefact_build_id=artefact_build_id,
            environment_id=environment_id,
            review_decision=review_decision,
            review_comment=review_comment,
        )
        self._add_object(review)
        return review

    def _add_object(self, instance: object) -> None:
        self.db_session.add(instance)
        self.db_session.commit()
        self.db_session.expire_all()
