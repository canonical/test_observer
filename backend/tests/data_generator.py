# Copyright (C) 2023 Canonical Ltd.
#
# This file is part of Test Observer Backend.
#
# Test Observer Backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# Test Observer Backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


from datetime import date, datetime

from sqlalchemy.orm import Session

from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    ArtefactBuildEnvironmentReview,
    Environment,
    TestCase,
    TestEvent,
    TestExecution,
    TestExecutionRerunRequest,
    TestResult,
    User,
)
from test_observer.data_access.models_enums import (
    ArtefactBuildEnvironmentReviewDecision,
    ArtefactStatus,
    FamilyName,
    StageName,
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
        stage: StageName = StageName.beta,
        family: FamilyName = FamilyName.snap,
        name: str = "core",
        version: str = "1.1.1",
        track: str = "",
        store: str = "",
        series: str = "",
        repo: str = "",
        created_at: datetime | None = None,
        status: ArtefactStatus = ArtefactStatus.UNDECIDED,
        archived: bool = False,
        bug_link: str = "",
        due_date: date | None = None,
        assignee_id: int | None = None,
    ) -> Artefact:
        family = FamilyName(family)

        match family:
            case FamilyName.snap:
                track = track or "latest"
                store = store or "ubuntu"
            case FamilyName.deb:
                series = series or "jammy"
                repo = repo or "main"
            case FamilyName.charm:
                track = track or "latest"

        created_at = created_at or datetime.utcnow()

        artefact = Artefact(
            name=name,
            stage=stage,
            family=family,
            version=version,
            track=track,
            store=store,
            series=series,
            repo=repo,
            created_at=created_at,
            status=status,
            archived=archived,
            bug_link=bug_link,
            due_date=due_date,
            assignee_id=assignee_id,
        )
        self._add_object(artefact)
        return artefact

    def gen_image(
        self,
        stage: StageName = StageName.pending,
        name: str = "noble-desktop-amd64",
        version: str = "20240827",
        os: str = "ubuntu",
        release: str = "noble",
        sha256: str = "e71fb5681e63330445eec6fc3fe043f36"
        "5289c2e595e3ceeac08fbeccfb9a957",
        owner: str = "foundations",
        image_url: str = (
            "https://cdimage.ubuntu.com/noble/daily-live/20240827/noble-desktop-amd64.iso"
        ),
        created_at: datetime | None = None,
        status: ArtefactStatus = ArtefactStatus.UNDECIDED,
        bug_link: str = "",
        due_date: date | None = None,
        assignee_id: int | None = None,
    ):
        image = Artefact(
            name=name,
            stage=stage,
            family=FamilyName.image,
            version=version,
            os=os,
            release=release,
            sha256=sha256,
            owner=owner,
            image_url=image_url,
            created_at=created_at,
            status=status,
            bug_link=bug_link,
            due_date=due_date,
            assignee_id=assignee_id,
        )
        self._add_object(image)
        return image

    def gen_artefact_build(
        self,
        artefact: Artefact,
        architecture: str = DEFAULT_ARCHITECTURE,
        revision: int | None = None,
    ) -> ArtefactBuild:
        match artefact.family:
            case FamilyName.snap | FamilyName.charm:
                revision = revision or 1

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
        checkbox_version: str | None = None,
        created_at: datetime | None = None,
        test_plan: str | None = "Test plan",
    ) -> TestExecution:
        test_execution = TestExecution(
            artefact_build=artefact_build,
            environment=environment,
            ci_link=ci_link,
            c3_link=c3_link,
            status=status,
            checkbox_version=checkbox_version,
            created_at=created_at,
            test_plan=test_plan,
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
        artefact_build: ArtefactBuild,
        environment: Environment,
        review_decision: list[ArtefactBuildEnvironmentReviewDecision] | None = None,
        review_comment: str = "",
    ):
        review = ArtefactBuildEnvironmentReview(
            artefact_build=artefact_build,
            environment=environment,
            review_decision=review_decision,
            review_comment=review_comment,
        )
        self._add_object(review)
        return review

    def gen_test_event(
        self,
        test_execution: TestExecution,
        event_name: str,
        timestamp: datetime = datetime.now(),
        detail: str = "",
    ) -> TestEvent:
        test_event = TestEvent(
            test_execution=test_execution,
            event_name=event_name,
            timestamp=timestamp,
            detail=detail,
        )
        self._add_object(test_event)
        return test_event

    def _add_object(self, instance: object) -> None:
        self.db_session.add(instance)
        self.db_session.commit()
