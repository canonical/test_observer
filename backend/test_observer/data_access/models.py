# Copyright 2023 Canonical Ltd.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Written by:
#        Nadzeya Hutsko <nadzeya.hutsko@canonical.com>
#        Omar Selo <omar.selo@canonical.com>
from datetime import date, datetime
from typing import TypeVar

from sqlalchemy import (
    Enum,
    ForeignKey,
    Index,
    MetaData,
    String,
    UniqueConstraint,
    column,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.sql import func

from test_observer.data_access.models_enums import (
    ArtefactStatus,
    TestExecutionReviewDecision,
    TestExecutionStatus,
    TestResultStatus,
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


class User(Base):
    """
    ORM representing users that can be assigned to review artefacts
    """

    # user is a reserved name in PostgreSQL
    __tablename__ = "app_user"

    launchpad_email: Mapped[str] = mapped_column(unique=True)
    launchpad_handle: Mapped[str]
    name: Mapped[str]

    assignments: Mapped[list["Artefact"]] = relationship(back_populates="assignee")

    def __repr__(self) -> str:
        return data_model_repr(self, "launchpad_handle")


class Family(Base):
    """A model to represent artefact family object"""

    __tablename__ = "family"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    # Relationships
    stages: Mapped[list["Stage"]] = relationship(
        back_populates="family", cascade="all, delete", order_by="Stage.position"
    )

    def __repr__(self) -> str:
        return data_model_repr(self, "name")


class Stage(Base):
    """A model to represent artefact stage in the promotion cycle"""

    __tablename__ = "stage"

    name: Mapped[str] = mapped_column(String(100), index=True)
    position: Mapped[int] = mapped_column()
    # Relationships
    family_id: Mapped[int] = mapped_column(ForeignKey("family.id", ondelete="CASCADE"))
    family: Mapped[Family] = relationship(back_populates="stages")
    artefacts: Mapped[list["Artefact"]] = relationship(
        back_populates="stage", cascade="all, delete"
    )

    def __repr__(self) -> str:
        return data_model_repr(self, "name", "position", "family_id")


class Artefact(Base):
    """A model to represent artefacts (snaps, debs, images)"""

    __tablename__ = "artefact"

    name: Mapped[str] = mapped_column(String(200), index=True)
    version: Mapped[str]
    track: Mapped[str | None]
    store: Mapped[str | None]
    series: Mapped[str | None]
    repo: Mapped[str | None]
    # Relationships
    stage_id: Mapped[int] = mapped_column(ForeignKey("stage.id", ondelete="CASCADE"))
    stage: Mapped[Stage] = relationship(back_populates="artefacts")
    builds: Mapped[list["ArtefactBuild"]] = relationship(
        back_populates="artefact", cascade="all, delete"
    )
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("app_user.id"))
    assignee: Mapped[User | None] = relationship(back_populates="assignments")
    # Default fields
    due_date: Mapped[date | None]
    status: Mapped[ArtefactStatus] = mapped_column(default=ArtefactStatus.UNDECIDED)

    __table_args__ = (
        UniqueConstraint("name", "version", "track", name="unique_snap"),
        UniqueConstraint("name", "version", "series", "repo", name="unique_deb"),
    )

    def __repr__(self) -> str:
        return data_model_repr(
            self,
            "name",
            "version",
            "track",
            "store",
            "series",
            "repo",
            "stage_id",
            "due_date",
            "status",
        )


class ArtefactBuild(Base):
    """A model to represent specific builds of artefact (e.g. arm64 revision 2)"""

    __tablename__ = "artefact_build"

    architecture: Mapped[str] = mapped_column(String(100), index=True)
    revision: Mapped[int | None]
    # Relationships
    artefact_id: Mapped[int] = mapped_column(
        ForeignKey("artefact.id", ondelete="CASCADE")
    )
    artefact: Mapped[Artefact] = relationship(
        back_populates="builds", foreign_keys=[artefact_id]
    )
    test_executions: Mapped[list["TestExecution"]] = relationship(
        back_populates="artefact_build", cascade="all, delete"
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

    name: Mapped[str] = mapped_column(String(200))
    architecture: Mapped[str] = mapped_column(String(100))
    test_executions: Mapped[list["TestExecution"]] = relationship(
        back_populates="environment"
    )

    __table_args__ = (UniqueConstraint("name", "architecture"),)

    def __repr__(self) -> str:
        return data_model_repr(self, "name", "architecture")


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
        ForeignKey("artefact_build.id", ondelete="CASCADE")
    )
    artefact_build: Mapped["ArtefactBuild"] = relationship(
        back_populates="test_executions"
    )
    environment_id: Mapped[int] = mapped_column(ForeignKey("environment.id"))
    environment: Mapped["Environment"] = relationship(back_populates="test_executions")
    test_results: Mapped[list["TestResult"]] = relationship(
        back_populates="test_execution", cascade="all, delete"
    )
    # Default fields
    status: Mapped[TestExecutionStatus] = mapped_column(
        default=TestExecutionStatus.NOT_STARTED
    )
    review_decision: Mapped[list[TestExecutionReviewDecision]] = mapped_column(
        ARRAY(Enum(TestExecutionReviewDecision)),
        default=[],
    )
    review_comment: Mapped[str] = mapped_column(default="")

    __table_args__ = (UniqueConstraint("artefact_build_id", "environment_id"),)

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
    category: Mapped[str]

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

    def __repr__(self) -> str:
        return data_model_repr(
            self,
            "status",
            "comment",
            "io_log",
            "test_execution_id",
            "test_case_id",
        )
