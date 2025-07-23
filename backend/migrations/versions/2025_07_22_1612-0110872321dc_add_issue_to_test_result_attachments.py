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

"""Add issue to test result attachments

Revision ID: 0110872321dc
Revises: ab74101e7373
Create Date: 2025-07-22 16:12:22.752629+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0110872321dc"
down_revision = "ab74101e7373"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "issue_test_result_attachment",
        sa.Column("issue_id", sa.Integer(), nullable=False),
        sa.Column("test_result_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["issue_id"],
            ["issue.id"],
            name=op.f("issue_test_result_attachment_issue_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["test_result_id"],
            ["test_result.id"],
            name=op.f("issue_test_result_attachment_test_result_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("issue_test_result_attachment_pkey"),
        ),
        sa.UniqueConstraint(
            "issue_id",
            "test_result_id",
            name=op.f("issue_test_result_attachment_issue_id_test_result_id_key"),
        ),
    )
    op.create_index(
        op.f("issue_test_result_attachment_issue_id_ix"),
        "issue_test_result_attachment",
        ["issue_id"],
        unique=False,
    )
    op.create_index(
        op.f("issue_test_result_attachment_test_result_id_ix"),
        "issue_test_result_attachment",
        ["test_result_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("issue_test_result_attachment")
