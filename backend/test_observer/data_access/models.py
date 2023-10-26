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
from itertools import groupby
from operator import attrgetter
from typing import TypeVar

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, column
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.sql import func

from test_observer.data_access.models_enums import (
    ArtefactStatus,
    TestExecutionStatus,
)


class Base(DeclarativeBase):
    """Base model for all the models"""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )


DataModel = TypeVar("DataModel", bound=Base)


def data_model_repr(obj: DataModel, *keys: str) -> str:
    all_keys = ("id", "created_at", "updated_at") + keys
    kwargs = [f"{key}={getattr(obj, key)!r}" for key in all_keys]
    return f"{type(obj).__name__}({', '.join(kwargs)})"


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

    @property
    def latest_artefacts(self) -> list["Artefact"]:
        artefact_groups = groupby(self.artefacts, attrgetter("name", "source"))

        return [
            max(artefacts, key=attrgetter("created_at"))
            for _, artefacts in artefact_groups
        ]

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
    # Default fields
    due_date: Mapped[date | None]
    status: Mapped[ArtefactStatus | None]

    __table_args__ = (
        UniqueConstraint(
            "name", "version", "track", "series", "repo", name="unique_artefact"
        ),
    )

    def __repr__(self) -> str:
        return data_model_repr(
            self, "name", "version", "source", "stage_id", "due_date", "status"
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
            "idx_artefact_id_architecture_null_revision",
            "artefact_id",
            "architecture",
            unique=True,
            postgresql_where=(column("revision").is_(None)),
        ),
        # Unique constraint when revision is NOT NULL
        Index(
            "idx_artefact_id_architecture_revision",
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

    __tablename__ = "test_execution"

    jenkins_link: Mapped[str] = mapped_column(String(200), nullable=True)
    c3_link: Mapped[str] = mapped_column(String(200), nullable=True)
    # Relationships
    artefact_build_id: Mapped[int] = mapped_column(
        ForeignKey("artefact_build.id", ondelete="CASCADE")
    )
    artefact_build: Mapped["ArtefactBuild"] = relationship(
        back_populates="test_executions"
    )
    environment_id: Mapped[int] = mapped_column(ForeignKey("environment.id"))
    environment: Mapped["Environment"] = relationship(back_populates="test_executions")
    # Default fields
    status: Mapped[TestExecutionStatus] = mapped_column(
        default=TestExecutionStatus.NOT_STARTED
    )

    __table_args__ = (UniqueConstraint("artefact_build_id", "environment_id"),)

    def __repr__(self) -> str:
        return data_model_repr(
            self,
            "artefact_build_id",
            "environment_id",
            "status",
            "jenkins_link",
            "c3_link",
        )
