# Copyright (C) 2023-2025 Canonical Ltd.
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


"""Create test execution rerun requests table

Revision ID: 08bc88dcb1e1
Revises: 5d36de5a8a48
Create Date: 2024-04-30 09:26:48.766175+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "08bc88dcb1e1"
down_revision = "5d36de5a8a48"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "test_execution_rerun_request",
        sa.Column("test_execution_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["test_execution_id"],
            ["test_execution.id"],
            name=op.f("test_execution_rerun_request_test_execution_id_fkey"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("test_execution_rerun_request_pkey")),
        sa.UniqueConstraint(
            "test_execution_id",
            name=op.f("test_execution_rerun_request_test_execution_id_key"),
        ),
    )


def downgrade() -> None:
    op.drop_table("test_execution_rerun_request")
