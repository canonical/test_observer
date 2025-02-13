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


"""Add TestCaseIssue table

Revision ID: ba6550a03bc8
Revises: 2745d4e5bc72
Create Date: 2024-08-30 13:03:39.864116+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ba6550a03bc8"
down_revision = "2745d4e5bc72"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "test_case_issue",
        sa.Column("template_id", sa.String(), nullable=False),
        sa.Column("case_name", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("test_case_issue_pkey")),
    )
    op.create_index(
        op.f("test_case_issue_case_name_ix"),
        "test_case_issue",
        ["case_name"],
        unique=False,
    )
    op.create_index(
        op.f("test_case_issue_template_id_ix"),
        "test_case_issue",
        ["template_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("test_case_issue_template_id_ix"), table_name="test_case_issue")
    op.drop_index(op.f("test_case_issue_case_name_ix"), table_name="test_case_issue")
    op.drop_table("test_case_issue")
