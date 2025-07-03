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


"""Test services functions"""

from datetime import datetime, timedelta, UTC

from sqlalchemy.orm import Session

from test_observer.data_access.models_enums import FamilyName, StageName
from test_observer.data_access.repository import (
    get_artefacts_by_family, create_test_execution_relevant_link
)
from tests.data_generator import DataGenerator

from pydantic import HttpUrl


def test_get_artefacts_by_family_latest(db_session: Session, generator: DataGenerator):
    """We should get a only latest artefacts in each stage for the specified family"""
    # Arrange
    artefact_tuple = [
        ("core20", FamilyName.snap, StageName.edge, datetime.utcnow(), "1"),
        ("oem-jammy", FamilyName.deb, StageName.proposed, datetime.utcnow(), "1"),
        (
            "core20",
            FamilyName.snap,
            StageName.edge,
            datetime.utcnow() - timedelta(days=10),
            "2",
        ),
        (
            "core20",
            FamilyName.snap,
            StageName.beta,
            datetime.utcnow() - timedelta(days=20),
            "3",
        ),
    ]
    expected_artefacts = {artefact_tuple[0], artefact_tuple[-1]}

    for name, family, stage, created_at, version in artefact_tuple:
        generator.gen_artefact(
            stage,
            family=family,
            name=name,
            created_at=created_at,
            version=version,
        )

    # Act
    artefacts = get_artefacts_by_family(db_session, FamilyName.snap)

    # Assert
    assert len(artefacts) == len(expected_artefacts)
    assert {
        (
            artefact.name,
            artefact.family,
            artefact.stage,
            artefact.created_at,
            artefact.version,
        )
        for artefact in artefacts
    } == expected_artefacts


def test_get_artefacts_by_family_charm_unique(
    db_session: Session, generator: DataGenerator
):
    """For charms, artefacts should be returned using the archived field"""
    # Arrange
    specs = [
        ("name-1", "1", False),
        ("name-1", "2", True),
        ("name-2", "3", False),
    ]
    for name, version, archived in specs:
        artefact = generator.gen_artefact(
            StageName.edge,
            family=FamilyName.charm,
            name=name,
            version=version,
            archived=archived,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        generator.gen_artefact_build(
            artefact,
            "arch-1",
        )
    expected_artefacts = {specs[0], specs[2]}

    # Act
    artefacts = get_artefacts_by_family(db_session, FamilyName.charm)

    # Assert
    assert len(artefacts) == len(expected_artefacts)
    assert {
        (
            artefact.name,
            artefact.version,
            artefact.archived,
        )
        for artefact in artefacts
    } == expected_artefacts

def test_create_test_execution_relevant_link(
    db_session: Session, generator: DataGenerator
):
    """Test creating a relevant link for a test execution."""
    # Arrange
    artefact = generator.gen_artefact()
    artefact_build = generator.gen_artefact_build(artefact=artefact)
    environment = generator.gen_environment()

    test_execution = generator.gen_test_execution(
        artefact_build=artefact_build,
        environment=environment
    )

    label = "Test Link"
    url = HttpUrl("https://example.com/test-link")

    # Act
    link = create_test_execution_relevant_link(
        db_session, test_execution.id, label, url
    )

    # Assert
    assert link.label == label
    assert HttpUrl(link.url) == url
    assert link.test_execution_id == test_execution.id
    assert link.created_at is not None
    db_session.refresh(test_execution)
    assert any(rl.id == link.id for rl in test_execution.relevant_links)