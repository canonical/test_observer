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

import json

from sqlalchemy import Connection, event, text
from sqlalchemy.orm import Session

_AUDIT_CONTEXT_KEY = "triggered_by"
_AUDIT_SETTING = "audit.triggered_by"


def _serialize_triggered_by(triggered_by: dict[str, dict[str, int] | str]) -> str:
    return json.dumps(triggered_by, separators=(",", ":"), sort_keys=True)


def _set_connection_audit_context(connection: Connection, triggered_by: dict[str, dict[str, int] | str]) -> None:
    connection.execute(
        text("SELECT set_config(:setting, :value, true)"),
        {"setting": _AUDIT_SETTING, "value": _serialize_triggered_by(triggered_by)},
    )


def set_audit_context(
    db: Session,
    *,
    user_id: int | None = None,
    application_id: int | None = None,
    automation: str | None = None,
) -> None:
    """Set and retain the transaction-local actor information for audited writes."""
    updates: dict[str, dict[str, int] | str] = {}
    if user_id is not None:
        updates["user"] = {"id": user_id}
    if application_id is not None:
        updates["application"] = {"id": application_id}
    if automation is not None:
        if not automation.strip():
            raise ValueError("automation must not be empty")
        updates["automation"] = automation
    if not updates:
        raise ValueError("At least one audit actor must be provided")

    triggered_by = db.info.setdefault(_AUDIT_CONTEXT_KEY, {})
    if not isinstance(triggered_by, dict):
        raise TypeError("Session audit context must be a dictionary")
    triggered_by.update(updates)
    _set_connection_audit_context(db.connection(), triggered_by)


def set_connection_audit_context(connection: Connection, *, automation: str) -> None:
    """Set transaction-local audit context for direct Core operations."""
    if not automation.strip():
        raise ValueError("automation must not be empty")
    _set_connection_audit_context(connection, {"automation": automation})


def _reapply_audit_context(session: Session, _transaction: object, connection: Connection) -> None:
    triggered_by = session.info.get(_AUDIT_CONTEXT_KEY)
    if triggered_by is not None:
        if not isinstance(triggered_by, dict):
            raise TypeError("Session audit context must be a dictionary")
        _set_connection_audit_context(connection, triggered_by)


def register_audit_context_listener() -> None:
    if not event.contains(Session, "after_begin", _reapply_audit_context):
        event.listen(Session, "after_begin", _reapply_audit_context)
