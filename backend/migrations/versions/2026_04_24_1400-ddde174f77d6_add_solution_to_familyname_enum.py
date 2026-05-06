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

"""Add solution to familyname enum

Revision ID: ddde174f77d6
Revises: daf0503863d7
Create Date: 2026-04-24 14:00:00.000000+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ddde174f77d6"
down_revision = "daf0503863d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE familyname ADD VALUE IF NOT EXISTS 'solution'")


def downgrade() -> None:
    drop_family_indexes()
    delete_rows_with_solution_family()

    op.execute("ALTER TYPE familyname RENAME TO familyname_old")
    op.execute("CREATE TYPE familyname AS ENUM('snap', 'deb', 'charm', 'image')")

    alter_columns_types_to_new_enum()
    op.execute("DROP TYPE familyname_old")

    add_family_indexes()


def alter_columns_types_to_new_enum() -> None:
    op.execute("ALTER TABLE artefact ALTER COLUMN family TYPE familyname USING family::text::familyname")
    op.execute(
        """ALTER TABLE issue_test_result_attachment_rule
        ALTER COLUMN families TYPE familyname[]
        USING families::text[]::familyname[]"""
    )
    op.execute("ALTER TABLE artefact_matching_rule ALTER COLUMN family TYPE familyname USING family::text::familyname")


def delete_rows_with_solution_family() -> None:
    op.execute("DELETE FROM artefact WHERE family = 'solution'")
    op.execute(
        """UPDATE issue_test_result_attachment_rule
        SET families = array_remove(families, 'solution')
        WHERE 'solution' = ANY(families)"""
    )
    op.execute("DELETE FROM artefact_matching_rule WHERE family = 'solution'")


def drop_family_indexes() -> None:
    op.execute("DROP INDEX IF EXISTS unique_image")
    op.execute("DROP INDEX IF EXISTS unique_deb")
    op.execute("DROP INDEX IF EXISTS unique_snap")
    op.execute("DROP INDEX IF EXISTS unique_charm")


def add_family_indexes() -> None:
    op.create_index(
        "unique_snap",
        "artefact",
        ["name", "version", "track", "branch"],
        unique=True,
        postgresql_where=sa.text("family = 'snap'"),
    )

    op.create_index(
        "unique_charm",
        "artefact",
        ["name", "version", "track", "branch"],
        unique=True,
        postgresql_where=sa.text("family = 'charm'"),
    )

    op.create_index(
        "unique_deb",
        "artefact",
        ["name", "version", "series", "repo", "source"],
        unique=True,
        postgresql_where=sa.text("family = 'deb'"),
    )

    op.create_index(
        "unique_image",
        "artefact",
        ["sha256"],
        unique=True,
        postgresql_where=sa.text("family = 'image'"),
    )
