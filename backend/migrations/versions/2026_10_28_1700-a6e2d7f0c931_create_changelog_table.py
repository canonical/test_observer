# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Create changelog table

Revision ID: a6e2d7f0c931
Revises: b7c2d9e4a1f0
Create Date: 2026-10-28 17:00:00.000000+00:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a6e2d7f0c931"
down_revision = "b7c2d9e4a1f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "changelog",
        sa.Column("change_time", sa.DateTime(), nullable=False),
        sa.Column(
            "entity",
            sa.Enum("ARTEFACT", "ARTEFACT_BUILD_ENVIRONMENT_REVIEW", name="changelogentity"),
            nullable=False,
        ),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column(
            "operation",
            sa.Enum("CREATE", "DELETE", "UPDATE", name="changelogoperation"),
            nullable=False,
        ),
        sa.Column("data_diff", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["app_user.id"],
            name=op.f("changelog_author_id_fkey"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("changelog_pkey")),
    )


def downgrade() -> None:
    op.drop_table("changelog")
    postgresql.ENUM(name="changelogentity").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="changelogoperation").drop(op.get_bind(), checkfirst=True)
