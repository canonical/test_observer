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


from collections import defaultdict
from datetime import date, datetime, timedelta
import secrets
from typing import TypeVar

from sqlalchemy import (
    Enum,
    ForeignKey,
    Index,
    MetaData,
    String,
    UniqueConstraint,
    column,
    Boolean,
    case,
    Table,
    Column,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.sql import func, ColumnElement

from test_observer.data_access.models_enums import (
    ArtefactBuildEnvironmentReviewDecision,
    ArtefactStatus,
    FamilyName,
    TestExecutionStatus,
    TestResultStatus,
    IssueSource,
    IssueStatus,
)


class Base(DeclarativeBase):
    """Base model for all the models"""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    metadata = MetaData(
        # Use a naming convention so that alembic knows the name of constraints
        # Use PostgreSQL specific conventions cause we already have keys named this way
        naming_convention={
            "ix": "%(table_name)s_%(column_0_N_name)s_ix",
            "uq": "%(table_name)s_%(column_0_N_name)s_key",
            "ck": "%(table_name)s_%(column_0_N_name)s_check",
            "fk": "%(table_name)s_%(column_0_N_name)s_fkey",
            "pk": "%(table_name)s_pkey",
        },
    )


DataModel = TypeVar("DataModel", bound=Base)


def data_model_repr(obj: DataModel, *keys: str) -> str:
    all_keys = ("id", "created_at", "updated_at") + keys
    kwargs = [f"{key}={getattr(obj, key)!r}" for key in all_keys]
    return f"{type(obj).__name__}({', '.join(kwargs)})"


team_users_association = Table(
    "team_users_association",
    Base.metadata,
    Column("user_id", ForeignKey("app_user.id"), primary_key=True),
    Column("team_id", ForeignKey("team.id"), primary_key=True),
)


class User(Base):
    """
    ORM representing users that can be assigned to review artefacts
    """

    # user is a reserved name in PostgreSQL
    __tablename__ = "app_user"

    email: Mapped[str] = mapped_column(unique=True)
    launchpad_handle: Mapped[str | None] = mapped_column(default=None)
    name: Mapped[str]
    is_reviewer: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool] = mapped_column(default=False)

    assignments: Mapped[list["Artefact"]] = relationship(back_populates="assignee")
    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user", cascade="all, delete"
    )
    teams: Mapped[list["Team"]] = relationship(
        secondary=team_users_association, back_populates="members"
    )

    def __repr__(self) -> str:
        return data_model_repr(self, "email", "name")


class Application(Base):
    __tablename__ = "application"

    name: Mapped[str] = mapped_column(unique=True)
    permissions: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    @staticmethod
    def gen_api_key() -> str:
        # prefix to_ is to indicate that this is an api key for Test Observer (TO)
        return f"to_{secrets.token_urlsafe(32)}"

    api_key: Mapped[str] = mapped_column(default=gen_api_key, unique=True)

    def __repr__(self) -> str:
        return data_model_repr(self, "name")


class Team(Base):
    """
    Launchpad teams that users can belong to. Currently, these are exposed by U1 SSO.
    Not all teams are exposed by U1 SSO, only those configured through U1 backend.
    """

    __tablename__ = "team"

    name: Mapped[str] = mapped_column(unique=True)
    permissions: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    members: Mapped[list[User]] = relationship(
        secondary=team_users_association, back_populates="teams"
    )

    def __repr__(self) -> str:
        return data_model_repr(self, "name")


class UserSession(Base):
    __tablename__ = "user_session"

    expires_at: Mapped[datetime] = mapped_column(
        default=datetime.now() + timedelta(days=14)
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE"), index=True
    )
    user: Mapped[User] = relationship(back_populates="sessions", foreign_keys=[user_id])


class Artefact(Base):
    """A model to represent artefacts (snaps, debs, images)"""

    __tablename__ = "artefact"

    # Generic fields
    name: Mapped[str] = mapped_column(String(200), index=True)
    version: Mapped[str]
    stage: Mapped[str] = mapped_column(String(100))
    family: Mapped[FamilyName]
    due_date: Mapped[date | None] = mapped_column(default=None)
    bug_link: Mapped[str] = mapped_column(default="")
    status: Mapped[ArtefactStatus] = mapped_column(default=ArtefactStatus.UNDECIDED)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    comment: Mapped[str] = mapped_column(default="")

    # Snap specific fields
    store: Mapped[str] = mapped_column(default="")

    # Snap and Charm specific fields
    track: Mapped[str] = mapped_column(default="")
    branch: Mapped[str] = mapped_column(String(200), default="")

    # Deb specific fields
    series: Mapped[str] = mapped_column(default="")
    repo: Mapped[str] = mapped_column(default="")
    source: Mapped[str] = mapped_column(String(200), default="")

    # Image specific fields
    os: Mapped[str] = mapped_column(String(200), default="")
    release: Mapped[str] = mapped_column(String(200), default="")
    sha256: Mapped[str] = mapped_column(String(200), default="")
    owner: Mapped[str] = mapped_column(String(200), default="")
    image_url: Mapped[str] = mapped_column(String(200), default="")

    # Relationships
    builds: Mapped[list["ArtefactBuild"]] = relationship(
        back_populates="artefact", cascade="all, delete"
    )
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("app_user.id"), index=True
    )
    assignee: Mapped[User | None] = relationship(back_populates="assignments")

    @property
    def architectures(self) -> set[str]:
        return {ab.architecture for ab in self.builds}

    __table_args__ = (
        Index(
            "unique_snap",
            "name",
            "version",
            "track",
            "branch",
            postgresql_where=column("family") == FamilyName.snap.name,
            unique=True,
        ),
        Index(
            "unique_charm",
            "name",
            "version",
            "track",
            "branch",
            postgresql_where=column("family") == FamilyName.charm.name,
            unique=True,
        ),
        Index(
            "unique_deb",
            "name",
            "version",
            "series",
            "repo",
            "source",
            postgresql_where=column("family") == FamilyName.deb.name,
            unique=True,
        ),
        Index(
            "unique_image",
            "sha256",
            postgresql_where=column("family") == FamilyName.image.name,
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return data_model_repr(
            self,
            "name",
            "version",
            "stage",
            "family",
            "track",
            "store",
            "branch",
            "series",
            "repo",
            "source",
            "os",
            "release",
            "sha256",
            "owner",
            "image_url",
            "due_date",
            "status",
            "archived",
        )

    @hybrid_property
    def is_kernel(self) -> bool:
        """Kernel artefacts start with 'linux-' or end with '-kernel'"""
        return self.name.startswith("linux-") or self.name.endswith("-kernel")

    @property
    def latest_builds(self) -> list["ArtefactBuild"]:
        # Group builds by architecture
        grouped_builds = defaultdict(list)
        for build in self.builds:
            grouped_builds[build.architecture].append(build)

        return [
            max(builds, key=lambda b: b.revision if b.revision else 0)
            for builds in grouped_builds.values()
        ]

    @property
    def all_environment_reviews_count(self) -> int:
        return sum(len(ab.environment_reviews) for ab in self.latest_builds)

    @property
    def completed_environment_reviews_count(self) -> int:
        return sum(
            len([er for er in ab.environment_reviews if er.review_decision])
            for ab in self.latest_builds
        )


class ArtefactBuild(Base):
    """A model to represent specific builds of artefact (e.g. arm64 revision 2)"""

    __tablename__ = "artefact_build"

    architecture: Mapped[str] = mapped_column(String(100), index=True)
    revision: Mapped[int | None]
    # Relationships
    artefact_id: Mapped[int] = mapped_column(
        ForeignKey("artefact.id", ondelete="CASCADE"), index=True
    )
    artefact: Mapped[Artefact] = relationship(
        back_populates="builds", foreign_keys=[artefact_id]
    )
    test_executions: Mapped[list["TestExecution"]] = relationship(
        back_populates="artefact_build", cascade="all, delete"
    )
    environment_reviews: Mapped[list["ArtefactBuildEnvironmentReview"]] = relationship(
        back_populates="artefact_build",
    )

    __table_args__ = (
        # Unique constraint when revision is NULL
        Index(
            None,
            "artefact_id",
            "architecture",
            unique=True,
            postgresql_where=(column("revision").is_(None)),
        ),
        # Unique constraint when revision is NOT NULL
        Index(
            None,
            "artefact_id",
            "architecture",
            "revision",
            unique=True,
            postgresql_where=(column("revision").isnot(None)),
        ),
    )

    def __repr__(self) -> str:
        return data_model_repr(self, "architecture", "revision", "artefact_id")


class Environment(Base):
    """
    A model to represent environment (usually physical devices but also
    can be more like containers)
    """

    __tablename__ = "environment"

    name: Mapped[str] = mapped_column(String(200), index=True)
    architecture: Mapped[str] = mapped_column(String(100), index=True)
    test_executions: Mapped[list["TestExecution"]] = relationship(
        back_populates="environment"
    )

    __table_args__ = (UniqueConstraint("name", "architecture"),)

    def __repr__(self) -> str:
        return data_model_repr(self, "name", "architecture")


class TestExecutionRerunRequest(Base):
    """
    Stores requests to rerun test executions.

    Reason for this being a separate table is to make fetching all such
    requests fast. Had we stored this as a column in TestExecution table then
    we'd need to scan all test executions to get this list.
    """

    __test__ = False
    __tablename__ = "test_execution_rerun_request"

    test_execution_id: Mapped[int] = mapped_column(
        ForeignKey("test_execution.id", ondelete="CASCADE"), unique=True
    )
    test_execution: Mapped["TestExecution"] = relationship(
        back_populates="rerun_request"
    )


test_execution_metadata_association_table = Table(
    "test_execution_metadata_association_table",
    Base.metadata,
    Column("test_execution_id", ForeignKey("test_execution.id"), primary_key=True),
    Column(
        "test_execution_metadata_id",
        ForeignKey("test_execution_metadata.id"),
        primary_key=True,
    ),
)


class TestExecutionMetadata(Base):
    """
    A table to store arbitrary metadata for test executions
    """

    __test__ = False
    __tablename__ = "test_execution_metadata"

    category: Mapped[str] = mapped_column(String(200))
    value: Mapped[str] = mapped_column(String(200))

    test_executions: Mapped[list["TestExecution"]] = relationship(
        secondary=test_execution_metadata_association_table,
        back_populates="execution_metadata",
    )

    __table_args__ = (UniqueConstraint("category", "value"),)


class TestExecution(Base):
    """
    A table to represent the result of test execution.
    It's the M2M relationship between Artefact and Environment tables
    """

    __test__ = False
    __tablename__ = "test_execution"

    ci_link: Mapped[str | None] = mapped_column(String(200), nullable=True, unique=True)
    c3_link: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Relationships
    artefact_build_id: Mapped[int] = mapped_column(
        ForeignKey("artefact_build.id", ondelete="CASCADE"), index=True
    )
    artefact_build: Mapped["ArtefactBuild"] = relationship(
        back_populates="test_executions"
    )
    environment_id: Mapped[int] = mapped_column(
        ForeignKey("environment.id"), index=True
    )
    environment: Mapped["Environment"] = relationship(back_populates="test_executions")
    test_results: Mapped[list["TestResult"]] = relationship(
        back_populates="test_execution", cascade="all, delete"
    )
    test_events: Mapped[list["TestEvent"]] = relationship(
        back_populates="test_execution",
        cascade="all, delete",
        order_by="TestEvent.timestamp",
    )
    resource_url: Mapped[str] = mapped_column(default="")
    rerun_request: Mapped[TestExecutionRerunRequest | None] = relationship(
        back_populates="test_execution", cascade="all, delete"
    )
    # Default fields
    status: Mapped[TestExecutionStatus] = mapped_column(
        default=TestExecutionStatus.NOT_STARTED
    )

    checkbox_version: Mapped[str | None] = mapped_column(
        String(200), nullable=True, default=None
    )

    relevant_links: Mapped[list["TestExecutionRelevantLink"]] = relationship(
        back_populates="test_execution", cascade="all, delete-orphan"
    )

    test_plan: Mapped[str] = mapped_column(String(200))

    execution_metadata: Mapped[list["TestExecutionMetadata"]] = relationship(
        secondary=test_execution_metadata_association_table,
        back_populates="test_executions",
        cascade="all, delete",
    )

    @property
    def has_failures(self) -> bool:
        return any(tr.status == TestResultStatus.FAILED for tr in self.test_results) or all(tr.status == TestResultStatus.SKIPPED for tr in self.test_results)

    @property
    def is_triaged(self) -> bool:
        return all(
            len(tr.issue_attachments) > 0
            for tr in self.test_results
            if tr.status in (TestResultStatus.FAILED, TestResultStatus.SKIPPED)
        )

    def __repr__(self) -> str:
        return data_model_repr(
            self,
            "artefact_build_id",
            "environment_id",
            "status",
            "ci_link",
            "c3_link",
        )


class TestCase(Base):
    """
    A table to represent test cases (not the runs themselves)
    """

    __test__ = False
    __tablename__ = "test_case"

    name: Mapped[str] = mapped_column(unique=True)
    category: Mapped[str] = mapped_column(index=True)
    template_id: Mapped[str] = mapped_column(default="", index=True)

    def __repr__(self) -> str:
        return data_model_repr(self, "name", "category")


class TestResult(Base):
    """
    A table to represent individual test results/runs
    """

    __test__ = False
    __tablename__ = "test_result"

    status: Mapped[TestResultStatus]
    comment: Mapped[str]
    io_log: Mapped[str]

    __table_args__ = (Index(None, "created_at"),)

    test_execution_id: Mapped[int] = mapped_column(
        ForeignKey("test_execution.id", ondelete="CASCADE"), index=True
    )
    test_execution: Mapped["TestExecution"] = relationship(
        back_populates="test_results"
    )

    test_case_id: Mapped[int] = mapped_column(
        ForeignKey("test_case.id", ondelete="CASCADE"), index=True
    )
    test_case: Mapped["TestCase"] = relationship()

    issue_attachments: Mapped[list["IssueTestResultAttachment"]] = relationship(
        back_populates="test_result"
    )

    def __repr__(self) -> str:
        return data_model_repr(
            self,
            "status",
            "comment",
            "io_log",
            "test_execution_id",
            "test_case_id",
        )


class TestEvent(Base):
    """
    A table to represent test events that have ocurred during a job
    """

    __test__ = False
    __tablename__ = "test_event"

    event_name: Mapped[str]
    timestamp: Mapped[datetime]
    detail: Mapped[str]
    test_execution_id: Mapped[int] = mapped_column(
        ForeignKey("test_execution.id", ondelete="CASCADE"), index=True
    )
    test_execution: Mapped["TestExecution"] = relationship(back_populates="test_events")

    def __repr__(self) -> str:
        return data_model_repr(
            self,
            "event_name",
            "timestamp",
            "detail",
            "test_execution_id",
        )


class TestCaseIssue(Base):
    """
    A table to store issues reported on certain tests
    """

    __tablename__ = "test_case_issue"

    template_id: Mapped[str] = mapped_column(index=True)
    case_name: Mapped[str] = mapped_column(index=True)
    url: Mapped[str]
    description: Mapped[str]

    def __repr__(self) -> str:
        return data_model_repr(
            self,
            "template_id",
            "case_name",
            "url",
            "description",
        )


class EnvironmentIssue(Base):
    """
    A table to store issues reported on certain environments
    """

    __tablename__ = "environment_issue"

    environment_name: Mapped[str]
    url: Mapped[str | None] = mapped_column(default=None)
    description: Mapped[str]
    is_confirmed: Mapped[bool]

    def __repr__(self) -> str:
        return data_model_repr(
            self,
            "environment_name",
            "url",
            "description",
            "is_confirmed",
        )


class Issue(Base):
    """
    A table to store issues from external sources (Jira, GitHub, Launchpad)
    """

    __tablename__ = "issue"

    source: Mapped[IssueSource]
    project: Mapped[str] = mapped_column(String(200))
    key: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(default="")
    status: Mapped[IssueStatus] = mapped_column(default=IssueStatus.UNKNOWN)

    test_result_attachments: Mapped[list["IssueTestResultAttachment"]] = relationship(
        back_populates="issue", cascade="all, delete"
    )

    test_result_attachment_rules: Mapped[list["IssueTestResultAttachmentRule"]] = (
        relationship(back_populates="issue", cascade="all, delete")
    )

    def __repr__(self) -> str:
        return data_model_repr(
            self,
            "source",
            "project",
            "key",
            "title",
            "status",
        )

    __table_args__ = (UniqueConstraint("project", "source", "key"),)

    @hybrid_property
    def url(self) -> str:
        if self.source == IssueSource.GITHUB:
            return f"https://github.com/{self.project}/issues/{self.key}"
        elif self.source == IssueSource.JIRA:
            return f"https://warthogs.atlassian.net/browse/{self.project}-{self.key}"
        elif self.source == IssueSource.LAUNCHPAD:
            return f"https://bugs.launchpad.net/{self.project}/+bug/{self.key}"
        raise ValueError("Unrecognized issue source")

    @url.inplace.expression
    @classmethod
    def _url_expression(cls) -> ColumnElement[str]:
        return case(
            (
                cls.source == IssueSource.GITHUB,
                func.concat(
                    "https://github.com/",
                    cls.project,
                    "/issues/",
                    cls.key,
                ),
            ),
            (
                cls.source == IssueSource.JIRA,
                func.concat(
                    "https://warthogs.atlassian.net/browse/",
                    cls.project,
                    "-",
                    cls.key,
                ),
            ),
            (
                cls.source == IssueSource.LAUNCHPAD,
                func.concat(
                    "https://bugs.launchpad.net/",
                    cls.project,
                    "/+bug/",
                    cls.key,
                ),
            ),
            else_="https://invalid",
        )


class IssueTestResultAttachment(Base):
    """
    A table for attaching issues to test results
    """

    __tablename__ = "issue_test_result_attachment"

    issue_id: Mapped[int] = mapped_column(
        ForeignKey("issue.id", ondelete="CASCADE"), index=True
    )
    issue: Mapped["Issue"] = relationship(back_populates="test_result_attachments")

    test_result_id: Mapped[int] = mapped_column(
        ForeignKey("test_result.id", ondelete="CASCADE"), index=True
    )
    test_result: Mapped["TestResult"] = relationship(back_populates="issue_attachments")

    attachment_rule_id: Mapped[int] = mapped_column(
        ForeignKey("issue_test_result_attachment_rule.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    attachment_rule: Mapped["IssueTestResultAttachmentRule"] = relationship(
        back_populates="test_results"
    )

    __table_args__ = (UniqueConstraint("issue_id", "test_result_id"),)


class IssueTestResultAttachmentRule(Base):
    """
    A table to store attachment rules for automatically attaching issues to test results
    """

    __tablename__ = "issue_test_result_attachment_rule"

    issue_id: Mapped[int] = mapped_column(
        ForeignKey("issue.id", ondelete="CASCADE"), index=True
    )
    issue: Mapped["Issue"] = relationship(back_populates="test_result_attachment_rules")

    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    test_results: Mapped[list["IssueTestResultAttachment"]] = relationship(
        back_populates="attachment_rule"
    )

    families: Mapped[list[FamilyName]] = mapped_column(
        ARRAY(Enum(FamilyName)), default=list
    )
    environment_names: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    test_case_names: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    template_ids: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    execution_metadata: Mapped[
        list["IssueTestResultAttachmentRuleExecutionMetadata"]
    ] = relationship(back_populates="attachment_rule", cascade="all, delete")


class IssueTestResultAttachmentRuleExecutionMetadata(Base):
    """
    A table for attachment rules to match on execution metadata
    """

    __tablename__ = "issue_test_result_attachment_rule_execution_metadata"
    __table_args__ = (UniqueConstraint("attachment_rule_id", "category", "value"),)

    attachment_rule_id: Mapped[int] = mapped_column(
        ForeignKey("issue_test_result_attachment_rule.id", ondelete="CASCADE")
    )
    attachment_rule: Mapped["IssueTestResultAttachmentRule"] = relationship(
        back_populates="execution_metadata"
    )

    category: Mapped[str] = mapped_column(String(200))
    value: Mapped[str] = mapped_column(String(200))


class ArtefactBuildEnvironmentReview(Base):
    """
    A table to store review information for test runs on a combination
    of environment and artefact builds.
    """

    __tablename__ = "artefact_build_environment_review"
    __table_args__ = (UniqueConstraint("artefact_build_id", "environment_id"),)

    review_decision: Mapped[list[ArtefactBuildEnvironmentReviewDecision]] = (
        mapped_column(ARRAY(Enum(ArtefactBuildEnvironmentReviewDecision)), default=[])
    )
    review_comment: Mapped[str] = mapped_column(default="")

    environment_id: Mapped[int] = mapped_column(
        ForeignKey("environment.id", ondelete="CASCADE"), index=True
    )
    environment: Mapped["Environment"] = relationship()

    artefact_build_id: Mapped[int] = mapped_column(
        ForeignKey("artefact_build.id", ondelete="CASCADE"), index=True
    )
    artefact_build: Mapped["ArtefactBuild"] = relationship(
        back_populates="environment_reviews",
    )

    @property
    def is_approved(self) -> bool:
        return (len(self.review_decision) > 0) and (
            ArtefactBuildEnvironmentReviewDecision.REJECTED not in self.review_decision
        )


class TestExecutionRelevantLink(Base):
    __test__ = False
    __tablename__ = "test_execution_relevant_link"

    test_execution_id: Mapped[int] = mapped_column(
        ForeignKey("test_execution.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str]
    url: Mapped[str]

    test_execution: Mapped["TestExecution"] = relationship(
        back_populates="relevant_links"
    )
