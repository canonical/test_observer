# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the License along with this program.
# If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from test_observer.data_access.audit import (
    DEFAULT_AUTHOR_ID,
    set_audit_context,
    set_connection_audit_context,
)
from test_observer.data_access.models import ChangeAuthor
from tests.data_generator import DataGenerator


def _session_author_id(db_session: Session) -> int:
    return db_session.info["author_id"]


def _set_actor(db_session: Session, actor: tuple[str, int]) -> None:
    kind, actor_id = actor
    if kind == "user_id":
        set_audit_context(db_session, user_id=actor_id)
    else:
        set_audit_context(db_session, application_id=actor_id)


@pytest.mark.parametrize(
    "actors",
    [
        (("user_id", 12), ("application_id", 3)),
        (("application_id", 3), ("user_id", 12)),
    ],
)
def test_set_audit_context_uses_user_over_application_in_either_order(
    db_session: Session, actors: tuple[tuple[str, int], tuple[str, int]]
) -> None:
    _set_actor(db_session, actors[0])
    _set_actor(db_session, actors[1])

    context = db_session.info["_audit_author"]
    assert context["kind"] == "user_id"
    assert context["value"] == 12
    assert db_session.info["author_id"] == context["author_id"]
    assert db_session.scalar(text("SELECT current_setting('audit.author_id')::integer")) == context["author_id"]


def test_user_overrides_default_automation_and_application_overrides_automation(db_session: Session) -> None:
    set_audit_context(db_session, application_id=3)
    assert db_session.info["_audit_author"]["kind"] == "application_id"

    set_audit_context(db_session, user_id=12)
    assert db_session.info["_audit_author"]["kind"] == "user_id"


def test_same_priority_actor_replaces_previous_actor(db_session: Session) -> None:
    set_audit_context(db_session, user_id=12)
    set_audit_context(db_session, user_id=13)

    context = db_session.info["_audit_author"]
    assert context["kind"] == "user_id"
    assert context["value"] == 13
    assert db_session.scalar(text("SELECT current_setting('audit.author_id')::integer")) == context["author_id"]


def test_same_author_is_deduplicated(db_session: Session) -> None:
    set_audit_context(db_session, automation_name="tests")
    author_id = _session_author_id(db_session)

    set_audit_context(db_session, automation_name="tests")

    assert _session_author_id(db_session) == author_id
    assert db_session.scalar(text("SELECT count(*) FROM change_author WHERE automation_name = 'tests'")) == 1


def test_audit_context_is_reapplied_after_commit(db_session: Session) -> None:
    set_audit_context(db_session, user_id=12)
    expected_author_id = _session_author_id(db_session)
    db_session.commit()

    assert db_session.scalar(text("SELECT current_setting('audit.author_id')::integer")) == expected_author_id
    assert _session_author_id(db_session) == expected_author_id


def test_audit_context_is_resolved_again_after_rollback(db_session: Session) -> None:
    set_audit_context(db_session, automation_name="rollback-test")
    rolled_back_author_id = _session_author_id(db_session)

    db_session.rollback()
    current_author_id = db_session.scalar(text("SELECT current_setting('audit.author_id')::integer"))

    assert current_author_id == _session_author_id(db_session)
    assert current_author_id != rolled_back_author_id
    assert (
        db_session.scalar(text("SELECT id FROM change_author WHERE automation_name = 'rollback-test'"))
        == current_author_id
    )


def test_set_connection_audit_context_resolves_author(db_session: Session) -> None:
    set_connection_audit_context(db_session.connection(), automation_name="core-operation")

    assert db_session.scalar(text("SELECT current_setting('audit.author_id')::integer")) == db_session.scalar(
        text("SELECT id FROM change_author WHERE automation_name = 'core-operation'")
    )


def test_audit_author_keeps_deleted_user_id(db_session: Session, generator: DataGenerator) -> None:
    user = generator.gen_user(email="audit-author@example.com")
    db_session.flush()
    set_audit_context(db_session, user_id=user.id)
    author_id = _session_author_id(db_session)

    db_session.delete(user)
    db_session.flush()

    author = db_session.get(ChangeAuthor, author_id)
    assert author is not None
    assert author.user_id == user.id


def test_connections_default_to_the_empty_author(db_engine: Engine) -> None:
    current_author = text("SELECT current_setting('audit.author_id')::integer")
    with db_engine.connect() as connection:
        assert connection.scalar(current_author) == DEFAULT_AUTHOR_ID
        default_author = connection.execute(
            text("SELECT user_id, application_id, automation_name FROM change_author WHERE id = :id"),
            {"id": DEFAULT_AUTHOR_ID},
        ).one()
        assert tuple(default_author) == (None, None, None)

        set_connection_audit_context(connection, automation_name="temporary-author")
        assert connection.scalar(current_author) != DEFAULT_AUTHOR_ID
        connection.rollback()

        assert connection.scalar(current_author) == DEFAULT_AUTHOR_ID


def test_set_audit_context_requires_exactly_one_actor(db_session: Session) -> None:
    with pytest.raises(ValueError):
        set_audit_context(db_session)
    with pytest.raises(ValueError):
        set_audit_context(db_session, user_id=1, application_id=2)
    with pytest.raises(ValueError):
        set_audit_context(db_session, automation_name="")
    with pytest.raises(ValueError):
        set_audit_context(db_session, automation_name="  ")


@pytest.mark.parametrize(
    "actor_values",
    [
        (None, None, "  "),
        (1, None, "multiple-actors"),
    ],
)
def test_change_author_constraints_reject_invalid_actors(
    db_session: Session, actor_values: tuple[int | None, int | None, str | None]
) -> None:
    with pytest.raises(DBAPIError, match="violates check constraint"), db_session.begin_nested():
        db_session.execute(
            text(
                "INSERT INTO change_author "
                "(user_id, application_id, automation_name, created_at, updated_at) "
                "VALUES (:user_id, :application_id, :automation_name, now(), now())"
            ),
            {
                "user_id": actor_values[0],
                "application_id": actor_values[1],
                "automation_name": actor_values[2],
            },
        )


def test_change_author_has_unique_actor_columns(db_session: Session) -> None:
    duplicate_pairs = [
        (ChangeAuthor(user_id=414141), ChangeAuthor(user_id=414141)),
        (ChangeAuthor(application_id=424242), ChangeAuthor(application_id=424242)),
        (ChangeAuthor(automation_name="unique-test"), ChangeAuthor(automation_name="unique-test")),
    ]
    for author, duplicate in duplicate_pairs:
        db_session.add(author)
        db_session.flush()

        with pytest.raises(IntegrityError), db_session.begin_nested():
            db_session.add(duplicate)
            db_session.flush()
