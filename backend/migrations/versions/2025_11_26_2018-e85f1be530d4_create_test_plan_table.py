# Copyright (C) 2023 Canonical Ltd.
#
# This file is part of Test Observer Backend.
#
# Test Observer Backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# Test Observer Backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""create_test_plan_table

Revision ID: e85f1be530d4
Revises: 3f6a99085db7
Create Date: 2025-11-26 20:18:06.935230+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e85f1be530d4"
down_revision = "3f6a99085db7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create test_plan table - just a normalized list of test plan names
    op.create_table(
        "test_plan",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
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
