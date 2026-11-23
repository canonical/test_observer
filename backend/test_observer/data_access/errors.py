# Copyright 2026 Canonical Ltd.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from sqlalchemy.exc import DBAPIError


def postgres_error_details(error: DBAPIError) -> tuple[str | None, str | None]:
    """Extract SQLSTATE and constraint name from pg8000 or psycopg diagnostics."""
    original = error.orig
    if original is None:
        return None, None
    details = original.args[0] if original.args and isinstance(original.args[0], dict) else {}
    diag = getattr(original, "diag", None)
    sqlstate = details.get("C") or getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
    name = details.get("n") or getattr(diag, "constraint_name", None)
    return sqlstate, name


def is_constraint_violation(error: DBAPIError, code: str, constraint: str) -> bool:
    return postgres_error_details(error) == (code, constraint)
