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

"""add_test_plan_id_to_test_execution

Revision ID: b329c0aa09ac
Revises: e85f1be530d4
Create Date: 2025-11-26 20:19:26.684626+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b329c0aa09ac"
down_revision = "e85f1be530d4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add test_plan_id column (nullable initially)
    op.add_column(
        "test_execution", sa.Column("test_plan_id", sa.Integer(), nullable=True)
    )

    # Populate test_plan_id by looking up test_plan name
    op.execute("""
        UPDATE test_execution te
        SET test_plan_id = tp.id
        FROM test_plan tp
        WHERE te.test_plan = tp.name
    """)

    # Make test_plan_id NOT NULL
    op.alter_column("test_execution", "test_plan_id", nullable=False)

    # Add foreign key and index
    op.create_foreign_key(
        "fk_test_execution_test_plan_id",
        "test_execution",
        "test_plan",
        ["test_plan_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        op.f("test_execution_test_plan_id_ix"), "test_execution", ["test_plan_id"]
    )

    # Drop old test_plan string column
    op.drop_column("test_execution", "test_plan")


def downgrade() -> None:
    # Re-add test_plan string column
    op.add_column(
        "test_execution", sa.Column("test_plan", sa.String(length=200), nullable=True)
    )

    # Populate from test_plan table
    op.execute("""
        UPDATE test_execution te
        SET test_plan = tp.name
        FROM test_plan tp
        WHERE te.test_plan_id = tp.id
    """)

    # Make test_plan NOT NULL
    op.alter_column("test_execution", "test_plan", nullable=False)

    # Drop foreign key, index, and test_plan_id column
    op.drop_index(op.f("test_execution_test_plan_id_ix"), table_name="test_execution")
    op.drop_constraint(
        "fk_test_execution_test_plan_id", "test_execution", type_="foreignkey"
    )
    op.drop_column("test_execution", "test_plan_id")
