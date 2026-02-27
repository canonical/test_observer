# Copyright 2023 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Test services functions"""

from typing import TypeVar

from pydantic import HttpUrl
from pytest import MonkeyPatch
from sqlalchemy.orm import Query, Session

from test_observer.data_access.models import TestCase
from test_observer.data_access.repository import (
    create_test_execution_relevant_link,
    get_or_create,
)
from tests.data_generator import DataGenerator

_T = TypeVar("_T")


def test_create_test_execution_relevant_link(db_session: Session, generator: DataGenerator):
    """Test creating a relevant link for a test execution."""
    # Arrange
    artefact = generator.gen_artefact()
    artefact_build = generator.gen_artefact_build(artefact=artefact)
    environment = generator.gen_environment()

    test_execution = generator.gen_test_execution(artefact_build=artefact_build, environment=environment)

    label = "Test Link"
    url = HttpUrl("https://example.com/test-link")

    # Act
    link = create_test_execution_relevant_link(db_session, test_execution.id, label, url)

    # Assert
    assert link.label == label
    assert HttpUrl(link.url) == url
    assert link.test_execution_id == test_execution.id
    assert link.created_at is not None
    db_session.refresh(test_execution)
    assert any(rl.id == link.id for rl in test_execution.relevant_links)


def test_get_or_create_returns_existing(db_session: Session):
    """Test that get_or_create returns an existing instance if it exists."""

    # Arrange
    test_case = TestCase(name="existing", category="category")
    db_session.add(test_case)
    db_session.commit()

    # Act
    result = get_or_create(
        db_session,
        model=type(test_case),
        filter_kwargs={
            "name": test_case.name,
            "category": test_case.category,
        },
    )

    assert test_case.id == result.id


def test_get_or_create_creates_new(db_session: Session):
    """Test that get_or_create creates a new instance if it doesn't exist."""

    # Arrange
    test_case = TestCase(name="new", category="category")

    # Act

    # Because of the way get_or_create attempts to create an instance,
    # we must make sure every required field of the model is included
    # in one of filter_kwargs or creation_kwargs
    # for the case when the model doesn't exist
    result = get_or_create(
        db_session,
        model=type(test_case),
        filter_kwargs={"name": test_case.name, "category": test_case.category},
    )

    assert result.id is not None
    assert result.name == test_case.name


def test_get_or_create_race_condition(
    db_session: Session,
    monkeypatch: MonkeyPatch,
):
    """
    Test that get_or_create handles a race condition,
    where another process creates the instance after we check for its existence
    but before we try to create it.
    """

    # Arrange

    # get_or_create calls query.first() to check if the instance exists,
    # so we mock the first() method to return None,
    # as if the instance did not exist
    def mock_first(_: Query[_T]) -> None:
        return None

    monkeypatch.setattr(Query, "first", mock_first)

    # We add the instance to the database to simulate another process creating it
    test_case = TestCase(name="new", category="category")
    db_session.add(test_case)
    db_session.commit()

    # We want to check that we raise the IntegrityError by checking calls to `one()`,
    # which only happens in the exception handling
    calls = {"one": 0}
    one = Query.one

    def mock_one(self: Query[_T]) -> _T:
        calls["one"] += 1
        return one(self)

    monkeypatch.setattr(Query, "one", mock_one)

    # Act

    # Because of the way get_or_create attempts to create an instance,
    # we must make sure every required field of the model is included
    # in one of filter_kwargs or creation_kwargs
    # for the case when the model doesn't exist
    result = get_or_create(
        db_session,
        model=type(test_case),
        filter_kwargs={"name": test_case.name, "category": test_case.category},
    )

    assert result.id == test_case.id
    assert calls["one"] == 1


def test_get_or_create_does_not_commit(
    db_session: Session,
):
    """Test that get_or_create does not commit the transaction."""

    # Arrange
    test_case_name = "new_uncommitted"
    test_case_category = "category"

    # Act - create instance using get_or_create
    result = get_or_create(
        db_session,
        model=TestCase,
        filter_kwargs={"name": test_case_name, "category": test_case_category},
    )

    # Assert - the instance should exist in the session
    assert result.id is not None
    assert result.name == test_case_name

    # But it should not be committed to the database
    # Rollback and verify the instance is gone
    db_session.rollback()

    # Query again - should not find the instance since it wasn't committed
    not_found = db_session.query(TestCase).filter_by(name=test_case_name, category=test_case_category).first()
    assert not_found is None
