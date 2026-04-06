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

"""Undo PostgreSQL Permissions enum.
This migration should essentially just undo the changes made in these migrations:

* 2026_03_23_1733-c29b4f545a9b_add_permissions_to_amrs.py
* 2026_03_31_1410-f0847700d32e_convert_permission_to_enum.py

Revision ID: dc384aedc33e
Revises: f0847700d32e
Create Date: 2026-04-05 15:35:45.285289+00:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "dc384aedc33e"
down_revision = "f0847700d32e"
branch_labels = None
depends_on = None

# Copied from 2026_03_23_1733-c29b4f545a9b_add_permissions_to_amrs.py
PERMISSION_VALUES = (
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
)
PERMISSION_ENUM = postgresql.ENUM(*PERMISSION_VALUES, name="permission")
PERMISSION_TYPE = postgresql.ARRAY(PERMISSION_ENUM)


def upgrade() -> None:
    # Drop the permission array default which uses the permission type
    op.execute("ALTER TABLE team ALTER COLUMN permissions DROP DEFAULT")

    # Convert the type from the PostgreSQL enum back to an array of strings
    op.alter_column(
        "team",
        "permissions",
        existing_type=PERMISSION_TYPE,
        type_=postgresql.ARRAY(sa.VARCHAR()),
        existing_nullable=False,
        postgresql_using="permissions::varchar[]",
    )

    # Restore the string array default
    op.execute("ALTER TABLE team ALTER COLUMN permissions SET DEFAULT '{}'::character varying[]")

    # Convert the type from the PostgreSQL enum back to an array of strings
    op.alter_column(
        "application",
        "permissions",
        existing_type=PERMISSION_TYPE,
        type_=postgresql.ARRAY(sa.VARCHAR()),
        existing_nullable=False,
        postgresql_using="permissions::varchar[]",
    )

    # Drop the permission array default which uses the permission type
    op.execute("ALTER TABLE artefact_matching_rule ALTER COLUMN grant_permissions DROP DEFAULT")

    # Convert the type from the PostgreSQL enum back to an array of strings
    op.alter_column(
        "artefact_matching_rule",
        "grant_permissions",
        existing_type=PERMISSION_TYPE,
        type_=postgresql.ARRAY(sa.VARCHAR()),
        existing_nullable=False,
        postgresql_using="grant_permissions::varchar[]",
    )

    # Set a string array default
    op.execute(
        "ALTER TABLE artefact_matching_rule ALTER COLUMN grant_permissions SET DEFAULT '{}'::character varying[]"
    )

    # Drop the PostgreSQL enum type
    PERMISSION_ENUM.drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    _assert_no_unknown_permission_values()

    # Create the permission type
    PERMISSION_ENUM.create(op.get_bind(), checkfirst=True)

    # Drop the string array default
    op.execute("ALTER TABLE artefact_matching_rule ALTER COLUMN grant_permissions DROP DEFAULT")

    # Convert the type from an array of strings to the PostgreSQL enum
    op.alter_column(
        "artefact_matching_rule",
        "grant_permissions",
        existing_type=postgresql.ARRAY(sa.VARCHAR()),
        type_=PERMISSION_TYPE,
        existing_nullable=False,
        postgresql_using="grant_permissions::permission[]",
    )

    # Restore the PostgreSQL enum array default
    op.execute("ALTER TABLE artefact_matching_rule ALTER COLUMN grant_permissions SET DEFAULT '{}'::permission[]")

    # Convert the type from an array of strings to the PostgreSQL enum
    op.alter_column(
        "application",
        "permissions",
        existing_type=postgresql.ARRAY(sa.VARCHAR()),
        type_=PERMISSION_TYPE,
        existing_nullable=False,
        postgresql_using="permissions::permission[]",
    )

    # Drop the string array default
    op.execute("ALTER TABLE team ALTER COLUMN permissions DROP DEFAULT")

    # Convert the type from an array of strings to the PostgreSQL enum
    op.alter_column(
        "team",
        "permissions",
        existing_type=postgresql.ARRAY(sa.VARCHAR()),
        type_=PERMISSION_TYPE,
        existing_nullable=False,
        postgresql_using="permissions::permission[]",
    )

    # Restore the PostgreSQL enum array default
    op.execute("ALTER TABLE team ALTER COLUMN permissions SET DEFAULT '{}'::permission[]")


def _assert_no_unknown_permission_values() -> None:
    """Fail downgrade clearly if varchar[] contains values missing from the enum."""
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            """
            WITH all_permissions AS (
                SELECT unnest(permissions) AS permission_value FROM team
                UNION ALL
                SELECT unnest(permissions) AS permission_value FROM application
                UNION ALL
                SELECT unnest(grant_permissions) AS permission_value FROM artefact_matching_rule
            )
            SELECT DISTINCT permission_value
            FROM all_permissions
            WHERE permission_value IS NOT NULL
              AND permission_value NOT IN :allowed_permissions
            ORDER BY permission_value
            """
        ).bindparams(sa.bindparam("allowed_permissions", expanding=True)),
        {"allowed_permissions": list(PERMISSION_VALUES)},
    )
    unknown_values = [row[0] for row in result]
    if unknown_values:
        raise RuntimeError(
            "Cannot downgrade permissions to PostgreSQL enum. Unknown permission values "
            f"found in database: {unknown_values}. Remove or map these values before downgrading."
        )
