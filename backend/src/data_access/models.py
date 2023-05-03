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
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
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
    """A model to represent artefact family object"""

    __tablename__ = "family"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    created_at: Mapped[timestamp]
    # Relationships
    stages: Mapped[List["Stage"]] = relationship(back_populates="family")
    arterfacts: Mapped[List["Artefact"]] = relationship(
        back_populates="family"
    )
    environments: Mapped[List["Environment"]] = relationship(
        back_populates="family"
    )


class Stage(Base):
    """A model to represent artefact stage in the promotion cycle"""

    __tablename__ = "stage"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    position: Mapped[int] = mapped_column(index=True)
    # Relationships
    family_id = mapped_column(ForeignKey("family.id"))
    family: Mapped[Family] = relationship(back_populates="stages")
    artefacts: Mapped[List["Artefact"]] = relationship(back_populates="stage")


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
    environments: Mapped[List["ExpectedEnvironment"]] = relationship(
        back_populates="artefact_group"
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
    family_id = mapped_column(ForeignKey("family.id"))
    family: Mapped[Family] = relationship(back_populates="artefacts")
    stage_id = mapped_column(ForeignKey("stage.id"))
    stage: Mapped[Stage] = relationship(back_populates="artefacts")
    artefact_group_id = mapped_column(ForeignKey("artefact_group.id"))
    artefact_group: Mapped[ArtefactGroup] = relationship(
        back_populates="artefacts"
    )
    environments: Mapped[List["TestExecution"]] = relationship(
        back_populates="artefact"
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
    families: Mapped[List["FamilyEnvironment"]] = relationship(
        back_populates="environment"
    )
    artefacts: Mapped[List["TestExecution"]] = relationship(
        back_populates="environment"
    )
    artefact_groups: Mapped[List["ExpectedEnvironment"]] = relationship(
        back_populates="environment"
    )


class TestExecution(Base):
    """
    A table to represent the result of test execution.
    It's the M2M relationship between Artefact and Environment tables
    """

    __tablename__ = "test_execution"

    artefact_id: Mapped[int] = mapped_column(
        ForeignKey("artefact.id"), primary_key=True
    )
    environment_id: Mapped[int] = mapped_column(
        ForeignKey("environment.id"), primary_key=True
    )
    jenkins_link: Mapped[str] = mapped_column(String(200), nullable=True)
    c3_link: Mapped[str] = mapped_column(String(200), nullable=True)
    updated_at: Mapped[timestamp] = mapped_column(onupdate=func.now())
    status: Mapped[str] = mapped_column(
        Enum(
            "Not Started",
            "In Progress",
            "Passed",
            "Failed",
            "Not Tested",
            name="test_status_enum",
        ),
        server_default="Not Started",
    )
    artefact: Mapped["Artefact"] = relationship(back_populates="environments")
    environment: Mapped["Environment"] = relationship(
        back_populates="artefacts"
    )


class ExpectedEnvironment(Base):
    """
    A table to represent the expected envoronments.
    It's the M2M relationship between ArtefactGroup and Environment tables
    """

    __tablename__ = "expected_environment"

    artefact_group_id: Mapped[int] = mapped_column(
        ForeignKey("artefact_group.id"), primary_key=True
    )
    environment_id: Mapped[int] = mapped_column(
        ForeignKey("environment.id"), primary_key=True
    )
    artefact_group: Mapped["ArtefactGroup"] = relationship(
        back_populates="environments"
    )
    environment: Mapped["Environment"] = relationship(
        back_populates="artefact_groups"
    )


class FamilyEnvironment(Base):
    """
    A table to represent the M2M relationship between Family and
    Environment tables
    """

    __tablename__ = "family_environment"

    family_id: Mapped[int] = mapped_column(
        ForeignKey("family.id"), primary_key=True
    )
    environment_id: Mapped[int] = mapped_column(
        ForeignKey("environment.id"), primary_key=True
    )
    family: Mapped["Family"] = relationship(back_populates="environments")
    environment: Mapped["Environment"] = relationship(back_populates="family")
