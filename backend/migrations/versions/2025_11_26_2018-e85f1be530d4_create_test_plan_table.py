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

"""create_test_plan_table

Revision ID: e85f1be530d4
Revises: 2ddd55f913eb
Create Date: 2025-11-26 20:18:06.935230+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e85f1be530d4"
down_revision = "2ddd55f913eb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create test_plan table - just a normalized list of test plan names
    op.create_table(
        "test_plan",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("test_plan_name_ix"), "test_plan", ["name"], unique=True)

    # Populate test_plan from existing test_execution data
    op.execute("""
        INSERT INTO test_plan (name)
        SELECT DISTINCT test_plan
        FROM test_execution
        WHERE test_plan IS NOT NULL
        ORDER BY test_plan
    """)


def downgrade() -> None:
    op.drop_index(op.f("test_plan_name_ix"), table_name="test_plan")
    op.drop_table("test_plan")
