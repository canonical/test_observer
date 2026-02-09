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

from sqlalchemy.orm import Query, Session, sessionmaker

from test_observer.data_access.repository import (
    create_test_execution_relevant_link,
    get_or_create,
)
from tests.data_generator import DataGenerator

from pydantic import HttpUrl
from pytest import MonkeyPatch


def test_create_test_execution_relevant_link(
    db_session: Session, generator: DataGenerator
):
    """Test creating a relevant link for a test execution."""
    # Arrange
    artefact = generator.gen_artefact()
    artefact_build = generator.gen_artefact_build(artefact=artefact)
    environment = generator.gen_environment()

    test_execution = generator.gen_test_execution(
        artefact_build=artefact_build, environment=environment
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

def test_get_or_create_returns_existing(db_session: Session, generator: DataGenerator):
    """Test that get_or_create returns an existing instance if it exists."""

    # Arrange
    test_case = generator.gen_test_case(name="unique")
    db_session.add(test_case)
    db_session.commit()

    # Act
    result = get_or_create(
        db_session,
        model=type(test_case),
        filter_kwargs={"name": test_case.name},
    )

    assert test_case.id == result.id

def test_get_or_create_creates_new(db_session: Session, generator: DataGenerator):
    """Test that get_or_create creates a new instance if it doesn't exist."""

    # Arrange
    test_case = generator.gen_test_case(name="unique")

    # Act
    result = get_or_create(
        db_session,
        model=type(test_case),
        filter_kwargs={"name": test_case.name},
    )

    assert result.id is not None
    assert result.name == test_case.name

def test_get_or_create_race_condition(db_session: Session, generator: DataGenerator, monkeypatch: MonkeyPatch):
    """
    Test that get_or_create handles a race condition,
    where another process creates the instance after we check for its existence 
    but before we try to create it.
    """
    
    # Arrange

    # get_or_create calls query.first() to check if the instance exists,
    # so we mock the first() method to return None,
    # as if the instance did not exist
    def mock_first():
        return None    
    monkeypatch.setattr(Query, "first", mock_first)

    # Then we add the instance to the database to simulate another process creating it
    test_case = generator.gen_test_case(name="race-condition")
    db_session.add(test_case)
    db_session.commit()

    # We want to check that we raise the IntegrityError by calling `db.flush()`
    calls = {"flush": 0}
    flush = db_session.flush
    def mock_flush():
        calls["flush"] += 1
        return flush()
    monkeypatch.setattr(db_session, "flush", mock_flush)

    # Act
    result = get_or_create(
        db_session,
        model=type(test_case),
        filter_kwargs={"name": test_case.name},
    )

    assert result.id == test_case.id
    assert db_session.query(type(test_case)).count() == 1
    assert calls["flush"] == 1
