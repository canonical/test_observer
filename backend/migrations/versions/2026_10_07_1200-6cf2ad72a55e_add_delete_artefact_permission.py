# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""add_delete_artefact_permission

Revision ID: 6cf2ad72a55e
Revises: f3a9c7d21b84
Create Date: 2026-10-07 12:00:00.000000+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6cf2ad72a55e"
down_revision = "f3a9c7d21b84"
branch_labels = None
depends_on = None

PERMISSION_ENUM_NAME = "permission"
OLD_PERMISSIONS = {
    "view_user",
    "change_user",
    "view_team",
    "change_team",
    "add_application",
    "change_application",
    "view_application",
    "view_permission",
    "view_issue",
    "change_issue",
    "change_issue_attachment",
    "change_issue_attachment_bulk",
    "change_attachment_rule",
    "change_auto_rerun",
    "view_test",
    "change_test",
    "view_rerun",
    "change_rerun",
    "change_rerun_bulk",
    "view_artefact",
    "change_artefact",
    "view_environment_review",
    "change_environment_review",
    "view_report",
    "view_test_case_reported_issue",
    "change_test_case_reported_issue",
    "view_environment_reported_issue",
    "change_environment_reported_issue",
    "view_notification",
    "change_notification",
    "view_sentry_debug",
}
NEW_PERMISSIONS = OLD_PERMISSIONS.union({"delete_artefact"})
COLUMNS_TO_UPDATE = [
    ("application", "permissions"),
    ("artefact_matching_rule", "grant_permissions"),
    ("team", "permissions"),
]


def _replace_permission_enum(old_permissions: set[str], new_permissions: set[str]) -> None:
    op.execute(f"ALTER TYPE {PERMISSION_ENUM_NAME} RENAME TO {PERMISSION_ENUM_NAME}_old")
    formatted_options = ", ".join(f"'{permission}'" for permission in sorted(new_permissions))
    op.execute(f"CREATE TYPE {PERMISSION_ENUM_NAME} AS ENUM ({formatted_options})")

    to_remove_values = old_permissions - new_permissions
    to_remove = ", ".join(f"'{permission}'" for permission in sorted(to_remove_values))
    for table_name, column_name in COLUMNS_TO_UPDATE:
        has_default = (
            op.get_bind()
            .execute(
                sa.text(
                    """
                    SELECT column_default
                    FROM information_schema.columns
                    WHERE table_name = :table_name AND column_name = :column_name
                    """
                ),
                {"table_name": table_name, "column_name": column_name},
            )
            .scalar()
        )
        if has_default:
            op.execute(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} DROP DEFAULT")

        if to_remove:
            op.execute(
                f"""
                UPDATE {table_name} SET {column_name} = COALESCE(
                    ARRAY(
                        SELECT val FROM unnest({column_name}) AS val
                        WHERE val::text NOT IN ({to_remove})
                    ), '{{}}'
                )
                WHERE {column_name}::text[] && ARRAY[{to_remove}]::text[]
                """
            )

        op.execute(
            f"""
            ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE {PERMISSION_ENUM_NAME}[]
            USING {column_name}::text[]::{PERMISSION_ENUM_NAME}[]
            """
        )
        if has_default:
            op.execute(
                f"ALTER TABLE {table_name} ALTER COLUMN {column_name} SET DEFAULT '{{}}'::{PERMISSION_ENUM_NAME}[]"
            )

    op.execute(f"DROP TYPE {PERMISSION_ENUM_NAME}_old")


def upgrade() -> None:
    _replace_permission_enum(OLD_PERMISSIONS, NEW_PERMISSIONS)


def downgrade() -> None:
    _replace_permission_enum(NEW_PERMISSIONS, OLD_PERMISSIONS)
