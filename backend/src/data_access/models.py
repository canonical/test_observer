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


from typing import List
from datetime import datetime, date

from sqlalchemy import (
    ForeignKey,
    Enum,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func, expression
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Base model for all the models"""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )


class Family(Base):
    """A model to represent artefact family object"""

    __tablename__ = "family"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    # Relationships
    stages: Mapped[List["Stage"]] = relationship(
        back_populates="family", cascade="all, delete-orphan"
    )


class Stage(Base):
    """A model to represent artefact stage in the promotion cycle"""

    __tablename__ = "stage"

    name: Mapped[str] = mapped_column(String(100), index=True)
    position: Mapped[int] = mapped_column()
    # Relationships
    family_id = mapped_column(ForeignKey("family.id"))
    family: Mapped[Family] = relationship(back_populates="stages")
    artefacts: Mapped[List["Artefact"]] = relationship(
        back_populates="stage", cascade="all, delete-orphan"
    )


class Artefact(Base):
    """A model to represent artefacts (snaps, debs, images)"""

    __tablename__ = "artefact"

    name: Mapped[str] = mapped_column(String(200), index=True)
    version: Mapped[str]
    source: Mapped[dict] = mapped_column(JSONB)
    # Relationships
    stage_id = mapped_column(ForeignKey("stage.id"))
    stage: Mapped[Stage] = relationship(back_populates="artefacts")
    builds: Mapped[List["ArtefactBuild"]] = relationship(
        back_populates="artefact", cascade="all, delete-orphan"
    )
    # Default fields
    due_date: Mapped[date | None]
    status: Mapped[str] = mapped_column(
        Enum("Approved", "Marked as Failed", name="artefact_status_enum"),
        nullable=True,
        default=None,
    )
    is_archived: Mapped[bool] = mapped_column(default=expression.false())

    __table_args__ = (
        UniqueConstraint("name", "version", "source", name="unique_artefact"),
    )


class ArtefactBuild(Base):
    """A model to represent specific builds of artefact (e.g. arm64 revision 2)"""

    __tablename__ = "artefact_build"

    architecture: Mapped[str] = mapped_column(String(100), index=True)
    revision: Mapped[int | None]
    # Relationships
    artefact_id: Mapped[int] = mapped_column(ForeignKey("artefact.id"))
    artefact: Mapped[Artefact] = relationship(
        back_populates="builds", foreign_keys=[artefact_id]
    )
    test_executions: Mapped[List["TestExecution"]] = relationship(
        back_populates="artefact_build", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("artefact_id", "architecture", "revision"),)


class Environment(Base):
    """
    A model to represent environment (usually physical devices but also
    can be more like containers)
    """

    __tablename__ = "environment"

    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    test_executions: Mapped[List["TestExecution"]] = relationship(
        back_populates="environment"
    )


class TestExecution(Base):
    """
    A table to represent the result of test execution.
    It's the M2M relationship between Artefact and Environment tables
    """

    __tablename__ = "test_execution"

    jenkins_link: Mapped[str] = mapped_column(String(200), nullable=True)
    c3_link: Mapped[str] = mapped_column(String(200), nullable=True)
    # Relationships
    artefact_build_id: Mapped[int] = mapped_column(ForeignKey("artefact_build.id"))
    artefact_build: Mapped["ArtefactBuild"] = relationship(
        back_populates="test_executions"
    )
    environment_id: Mapped[int] = mapped_column(ForeignKey("environment.id"))
    environment: Mapped["Environment"] = relationship(back_populates="test_executions")
    # Default fields
    status: Mapped[str] = mapped_column(
        Enum(
            "Not Started",
            "In Progress",
            "Passed",
            "Failed",
            "Not Tested",
            name="test_status_enum",
        ),
        default="Not Started",
    )

    __table_args__ = (UniqueConstraint("artefact_build_id", "environment_id"),)
