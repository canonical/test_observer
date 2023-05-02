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


from typing import List
from datetime import datetime
from typing_extensions import Annotated

from sqlalchemy import (
    Column,
    Table,
    ForeignKey,
    Enum,
    String,
    DateTime,
)
from sqlalchemy.sql import func, expression
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    DeclarativeBase,
    MappedAsDataclass,
    Mapped,
    mapped_column,
    relationship,
)


# DateTime custom type for mapped classes
timestamp = Annotated[
    datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]


class Base(MappedAsDataclass, DeclarativeBase):
    """Subclasses will be converted to dataclasses"""


class Family(Base):
    """A model to represent package family object"""

    __tablename__ = "family"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    created_at: Mapped[timestamp]
    # Relationships
    stages: Mapped[List["Stage"]] = relationship(back_populates="family")
    arterfacts: Mapped[List["Artefact"]] = relationship(back_populates="family")
    environments: Mapped[List["Environment"]] = relationship(
        back_populates="family"
    )


class Stage(Base):
    """A model to represent package stage in the promotion cycle"""

    __tablename__ = "stage"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    position: Mapped[int] = mapped_column(unique=True)
    # Relationships
    family: Mapped[Family] = relationship(back_populates="stages")
    arterfacts: Mapped[List["Artefact"]] = relationship(back_populates="stage")


# A table to represent the expected envoronments.
# It's the M2M relationship between ArtefactGroup and Environment tables
expected_environment = Table(
    "expected_environment",
    Base.metadata,
    Column(
        "artefact_group_id", ForeignKey("artefact_group.id"), primary_key=True
    ),
    Column("environment_id", ForeignKey("environment.id"), primary_key=True),
)


class ArtefactGroup(Base):
    """A model to represent groups of artefacts"""

    __tablename__ = "artefact_group"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    version_pattern: Mapped[str] = mapped_column(String(100))
    # Relationships
    artefacts: Mapped[List["Artefact"]] = relationship(
        back_populates="artefact_group"
    )
    environments: Mapped[List["Environment"]] = relationship(
        secondary=expected_environment, back_populates="artefact_groups"
    )


# A table to represent the result of test execution.
# It's the M2M relationship between Artefact and Environment tables
test_execution = Table(
    "test_execution",
    Base.metadata,
    Column("artefact_id", ForeignKey("artefact.id"), primary_key=True),
    Column("environment_id", ForeignKey("environment.id"), primary_key=True),
    Column("jenkins_link", String(200), nullable=True),
    Column("c3_link", String(200), nullable=True),
    Column("update_at", DateTime, onupdate=func.now()),
    Column(
        "status",
        Enum(
            "Not Started",
            "In Progress",
            "Passed",
            "Failed",
            name="test_status_enum",
        ),
        server_default="Not Started",
    ),
)


class Artefact(Base):
    """A model to represent artefacts (snaps, debs, images)"""

    __tablename__ = "artefact"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    source: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[timestamp]
    status: Mapped[str] = mapped_column(
        Enum("Approved", "Marked as Failed", name="artefact_status_enum"),
        nullable=True,
    )
    # Relationships
    family: Mapped[Family] = relationship(back_populates="artefacts")
    stage: Mapped[Stage] = relationship(back_populates="artefacts")
    artefact_group: Mapped[ArtefactGroup] = relationship(
        back_populates="artefacts"
    )
    environments: Mapped[List["Environment"]] = relationship(
        secondary=test_execution, back_populates="artefacts"
    )
    # Default fields
    is_archived: Mapped[bool] = mapped_column(
        server_default=expression.false()
    )


class Environment(Base):
    """
    A model to represent environment (usually physical devices but also
    can be more like containers)
    """

    __tablename__ = "environment"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    # Relationships
    family: Mapped[Family] = relationship(back_populates="environments")
    artefacts: Mapped[List["Artefact"]] = relationship(
        secondary=test_execution, back_populates="environments"
    )
    artefact_groups: Mapped[List["ArtefactGroup"]] = relationship(
        secondary=expected_environment, back_populates="environments"
    )
