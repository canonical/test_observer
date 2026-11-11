# Copyright 2026 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Connect application authors to database-level audit triggers.

set_audit_context() finds or inserts a change_author row, then sets its ID in the
transaction-local PostgreSQL setting ``audit.author_id`` using set_config().
Setting that value does not itself insert an audit row.

For models configured with the extension's @audit decorator and an ``author_id``
context column, the extension generates PostgreSQL triggers, installed through
Alembic migrations. On INSERT, UPDATE or DELETE, those triggers read
``current_setting('audit.author_id', false)`` and record it as ``audit_author_id``
alongside the row snapshot in the model's audit table. The audit row refers
to the change_author row created or found here.

Every new database connection starts with ``audit.author_id`` set at session
level to DEFAULT_AUTHOR_ID, the change_author row with no actor. Writes made
without an audit context are attributed to that row, and the transaction-local
value from set_audit_context() takes precedence while it is set.
"""

from sqlalchemy import Connection, Engine, event, text
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.orm import Session

_AUDIT_CONTEXT_KEY = "_audit_author"
_AUDIT_SETTING = "audit.author_id"

# The change_author row with no actor, seeded by migration c407ca4fb621.
DEFAULT_AUTHOR_ID = 1

type _Actor = tuple[str, int | str]
type _AuthorContext = dict[str, int | str]


def _validate_actor(
    *,
    user_id: int | None,
    application_id: int | None,
    automation_name: str | None,
) -> _Actor:
    actors = [
        ("user_id", user_id),
        ("application_id", application_id),
        ("automation_name", automation_name),
    ]
    provided = [(kind, value) for kind, value in actors if value is not None]
    if len(provided) != 1:
        raise ValueError("Exactly one audit actor must be provided")
    kind, value = provided[0]
    if kind == "automation_name" and (not isinstance(value, str) or not value.strip()):
        raise ValueError("automation_name must not be empty")
    if kind != "automation_name" and not isinstance(value, int):
        raise ValueError(f"{kind} must be an integer")
    return kind, value


def get_or_create_author(
    connection: Connection,
    *,
    user_id: int | None = None,
    application_id: int | None = None,
    automation_name: str | None = None,
) -> int:
    """Return the deduplicated author id for exactly one actor."""
    kind, value = _validate_actor(
        user_id=user_id,
        application_id=application_id,
        automation_name=automation_name,
    )
    select_author = text(f"SELECT id FROM change_author WHERE {kind} = :actor")
    author_id = connection.scalar(select_author, {"actor": value})
    if author_id is not None:
        return author_id

    insert_author = text(
        f"INSERT INTO change_author ({kind}, created_at, updated_at) VALUES (:actor, now(), now()) "
        f"ON CONFLICT ({kind}) DO NOTHING RETURNING id"
    )
    author_id = connection.scalar(insert_author, {"actor": value})
    if author_id is not None:
        return author_id

    author_id = connection.scalar(select_author, {"actor": value})
    if author_id is None:
        raise RuntimeError("Could not retrieve or create audit author")
    return author_id


def _resolve_author(connection: Connection, actor: _Actor) -> int:
    kind, value = actor
    if kind == "user_id":
        if not isinstance(value, int):
            raise TypeError("user_id must be an integer")
        return get_or_create_author(connection, user_id=value)
    if kind == "application_id":
        if not isinstance(value, int):
            raise TypeError("application_id must be an integer")
        return get_or_create_author(connection, application_id=value)
    if not isinstance(value, str):
        raise TypeError("automation_name must be a string")
    return get_or_create_author(connection, automation_name=value)


def _set_connection_audit_author(connection: Connection, author_id: int) -> None:
    connection.execute(
        text("SELECT set_config(:setting, :value, true)"),
        {"setting": _AUDIT_SETTING, "value": str(author_id)},
    )


def set_audit_context(
    db: Session,
    *,
    user_id: int | None = None,
    application_id: int | None = None,
    automation_name: str | None = None,
) -> None:
    """Set and retain the transaction-local author for audited writes."""
    kind, value = _validate_actor(
        user_id=user_id,
        application_id=application_id,
        automation_name=automation_name,
    )

    existing = db.info.get(_AUDIT_CONTEXT_KEY)
    if existing is not None:
        if not isinstance(existing, dict):
            raise TypeError("Session audit context must be a dictionary")
        priority = {"automation_name": 0, "application_id": 1, "user_id": 2}
        existing_kind = existing["kind"]
        if priority[kind] < priority[existing_kind]:
            return

    author_id = _resolve_author(db.connection(), (kind, value))
    context: _AuthorContext = {"kind": kind, "value": value, "author_id": author_id}
    db.info[_AUDIT_CONTEXT_KEY] = context
    db.info["author_id"] = author_id
    _set_connection_audit_author(db.connection(), author_id)


def set_connection_audit_context(connection: Connection, *, automation_name: str) -> None:
    """Set transaction-local audit context for direct Core operations.

    Used by seed_performance_data, which writes through a raw SQLAlchemy
    Connection rather than an ORM session.
    """
    author_id = get_or_create_author(connection, automation_name=automation_name)
    _set_connection_audit_author(connection, author_id)


def _reapply_audit_context(session: Session, _transaction: object, connection: Connection) -> None:
    context = session.info.get(_AUDIT_CONTEXT_KEY)
    if context is not None:
        if not isinstance(context, dict):
            raise TypeError("Session audit context must be a dictionary")
        kind, value = context["kind"], context["value"]
        if not isinstance(kind, str):
            raise TypeError("Session audit context kind must be a string")
        actor = (kind, value)
        author_id = _resolve_author(connection, actor)  # type: ignore[arg-type]
        context["author_id"] = author_id
        session.info["author_id"] = author_id
        _set_connection_audit_author(connection, author_id)


def _set_default_audit_author(dbapi_connection: DBAPIConnection, _connection_record: object) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute(f"SET {_AUDIT_SETTING} = '{DEFAULT_AUTHOR_ID}'")
    cursor.close()
    # Commit so that the session-level SET isn't undone by a rollback.
    dbapi_connection.commit()


def register_audit_context_listener() -> None:
    """Listens for the start of transactions to set the author again.

    The author in the context is set with `set_config(..., true)` so that
    the setting is not applied session-wide (which would be the case if the
    last argument were `false`) because database connections are pooled and
    reused (i.e. an author would carry over to the next request).

    However, because of this, the author setting only lasts until the
    transaction ends, so after `db.commit()` or `db.rollback()` the session's
    next write would run a new transaction with no author.

    This listener sets the author again once a new transaction start. A second
    listener sets DEFAULT_AUTHOR_ID on every new connection, as a fallback for
    writes without an audit context. They're registered in `data_access/setup.py`
    because that is the source of database-related utility in the backend.
    """
    if not event.contains(Engine, "connect", _set_default_audit_author):
        event.listen(Engine, "connect", _set_default_audit_author)
    if not event.contains(Session, "after_begin", _reapply_audit_context):
        event.listen(Session, "after_begin", _reapply_audit_context)
