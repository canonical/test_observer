# Copyright 2025 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Add test execution metadata

Revision ID: a23713521472
Revises: 0110872321dc
Create Date: 2025-07-23 19:47:49.937408+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a23713521472"
down_revision = "0110872321dc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "test_execution_metadata",
        sa.Column("category", sa.String(length=200), nullable=False),
        sa.Column("value", sa.String(length=200), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("test_execution_metadata_pkey")),
        sa.UniqueConstraint("category", "value", name=op.f("test_execution_metadata_category_value_key")),
    )
    op.create_table(
        "test_execution_metadata_association_table",
        sa.Column("test_execution_id", sa.Integer(), nullable=False),
        sa.Column("test_execution_metadata_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["test_execution_id"],
            ["test_execution.id"],
            name=op.f("test_execution_metadata_association_table_test_execution_id_fkey"),
        ),
        sa.ForeignKeyConstraint(
            ["test_execution_metadata_id"],
            ["test_execution_metadata.id"],
            name=op.f("test_execution_metadata_association_table_test_execution_metadata_id_fkey"),
        ),
        sa.PrimaryKeyConstraint(
            "test_execution_id",
            "test_execution_metadata_id",
            name=op.f("test_execution_metadata_association_table_pkey"),
        ),
    )


def downgrade() -> None:
    op.drop_table("test_execution_metadata_association_table")
    op.drop_table("test_execution_metadata")
