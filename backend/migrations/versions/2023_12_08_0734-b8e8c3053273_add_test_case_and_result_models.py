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


"""Add test case and result models

Revision ID: b8e8c3053273
Revises: 871eec26dc90
Create Date: 2023-12-08 07:34:01.696593+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b8e8c3053273"
down_revision = "871eec26dc90"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "test_case",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("test_case_pkey")),
        sa.UniqueConstraint("name", name=op.f("test_case_name_key")),
    )
    op.create_table(
        "test_result",
        sa.Column(
            "status",
            sa.Enum("PASSED", "FAILED", "SKIPPED", name="testresultstatus"),
            nullable=False,
        ),
        sa.Column("comment", sa.String(), nullable=False),
        sa.Column("io_log", sa.String(), nullable=False),
        sa.Column("test_execution_id", sa.Integer(), nullable=False),
        sa.Column("test_case_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["test_case_id"],
            ["test_case.id"],
            name=op.f("test_result_test_case_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["test_execution_id"],
            ["test_execution.id"],
            name=op.f("test_result_test_execution_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("test_result_pkey")),
    )
    op.create_index(
        op.f("test_result_test_case_id_ix"),
        "test_result",
        ["test_case_id"],
        unique=False,
    )
    op.create_index(
        op.f("test_result_test_execution_id_ix"),
        "test_result",
        ["test_execution_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("test_result_test_execution_id_ix"), table_name="test_result")
    op.drop_index(op.f("test_result_test_case_id_ix"), table_name="test_result")
    op.drop_table("test_result")
    op.drop_table("test_case")
    op.execute("DROP TYPE testresultstatus")
