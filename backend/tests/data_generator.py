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
    Application,
    Artefact,
    ArtefactBuild,
    ArtefactBuildEnvironmentReview,
    ArtefactMatchingRule,
    Environment,
    Issue,
    Team,
    TestCase,
    TestEvent,
    TestExecution,
    TestExecutionMetadata,
    TestExecutionRelevantLink,
    TestExecutionRerunRequest,
    TestPlan,
    TestResult,
    User,
    UserSession,
)
from test_observer.data_access.models_enums import (
    ArtefactBuildEnvironmentReviewDecision,
    ArtefactStatus,
    FamilyName,
    StageName,
    TestExecutionStatus,
    TestResultStatus,
    IssueSource,
    IssueStatus,
)

DEFAULT_ARCHITECTURE = "amd64"


class DataGenerator:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def gen_team(
        self,
        name: str = "canonical",
        permissions: list[str] | None = None,
        members: list[User] | None = None,
        artefact_matching_rules: list[ArtefactMatchingRule] | None = None,
    ) -> Team:
        team = Team(
            name=name,
            permissions=permissions or [],
            members=members or [],
        )
        self._add_object(team)
        
        # Add artefact matching rules if provided
        if artefact_matching_rules:
            for rule in artefact_matching_rules:
                if team not in rule.teams:
                    rule.teams.append(team)
            team.artefact_matching_rules = artefact_matching_rules
        
        return team

    def gen_artefact_matching_rule(
        self,
        family: FamilyName,
        stage: str | None = None,
        track: str | None = None,
        branch: str | None = None,
        teams: list[Team] = [],
    ) -> ArtefactMatchingRule:
        rule = ArtefactMatchingRule(
            family=family,
            stage=stage,
            track=track,
            branch=branch,
            teams=teams,
        )
        self._add_object(rule)
        return rule

    def gen_user(
        self,
        name: str = "John Doe",
        launchpad_handle: str | None = "jd",
        email: str = "john@doe.com",
        teams: list[Team] | None = None,
    ) -> User:
        user = User(
            name=name,
            email=email,
            launchpad_handle=launchpad_handle,
            teams=teams or [],
        )
        self._add_object(user)
        return user

    def gen_application(
        self,
        name: str = "somebot",
        permissions: list[str] | None = None,
    ) -> Application:
        application = Application(name=name, permissions=permissions or [])
        self._add_object(application)
        return application

    def gen_user_session(
        self, user: User, expires_at: datetime | None = None
    ) -> UserSession:
        session = UserSession(user=user)
        if expires_at:
            session.expires_at = expires_at
        self._add_object(session)
        return session

    def gen_artefact(
        self,
        stage: StageName = StageName.beta,
        family: FamilyName = FamilyName.snap,
        name: str = "core",
        version: str = "1.1.1",
        track: str = "",
        store: str = "",
        branch: str = "",
        series: str = "",
        repo: str = "",
        source: str = "",
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
            branch=branch,
            series=series,
            repo=repo,
            source=source,
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

    def gen_test_plan(self, name: str = "Test plan") -> TestPlan:
        test_plan = self.db_session.query(TestPlan).filter_by(name=name).first()
        if not test_plan:
            test_plan = TestPlan(name=name)
            self._add_object(test_plan)
        return test_plan

    def gen_test_execution(
        self,
        artefact_build: ArtefactBuild,
        environment: Environment,
        ci_link: str | None = None,
        c3_link: str | None = None,
        relevant_links: list[dict[str, str] | dict] | None = None,
        status: TestExecutionStatus = TestExecutionStatus.NOT_STARTED,
        checkbox_version: str | None = None,
        created_at: datetime | None = None,
        test_plan: str = "Test plan",
        execution_metadata: dict | None = None,
    ) -> TestExecution:
        if relevant_links is None:
            relevant_links = []
        converted_relevant_links = []
        for link_item in relevant_links:
            if isinstance(link_item, dict):
                converted_relevant_links.append(TestExecutionRelevantLink(**link_item))
            else:
                converted_relevant_links.append(link_item)

        execution_metadata_rows = []
        if execution_metadata:
            for category, values in execution_metadata.items():
                for value in values:
                    existing_row = (
                        self.db_session.query(TestExecutionMetadata)
                        .filter_by(category=category, value=value)
                        .first()
                    )
                    if existing_row:
                        execution_metadata_row = existing_row
                    else:
                        execution_metadata_row = TestExecutionMetadata(
                            category=category, value=value
                        )
                        self._add_object(execution_metadata_row)
                    execution_metadata_rows.append(execution_metadata_row)

        # Get or create TestPlan object
        test_plan_obj = self.gen_test_plan(test_plan)

        test_execution = TestExecution(
            artefact_build=artefact_build,
            environment=environment,
            ci_link=ci_link,
            c3_link=c3_link,
            relevant_links=converted_relevant_links,
            status=status,
            checkbox_version=checkbox_version,
            created_at=created_at,
            test_plan=test_plan_obj,
            execution_metadata=execution_metadata_rows,
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
        rerun = TestExecutionRerunRequest(
            test_plan_id=test_execution.test_plan_id,
            artefact_build_id=test_execution.artefact_build_id,
            environment_id=test_execution.environment_id,
        )
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

    def gen_issue(
        self,
        source: IssueSource = IssueSource.GITHUB,
        project: str = "canonical/test_observer",
        key: str = "42",
        title: str = "there is a bug",
        status: IssueStatus = IssueStatus.OPEN,
    ) -> Issue:
        issue = Issue(
            source=source,
            project=project,
            key=key,
            title=title,
            status=status,
        )
        self._add_object(issue)
        return issue

    def _add_object(self, instance: object) -> None:
        self.db_session.add(instance)
        self.db_session.commit()
