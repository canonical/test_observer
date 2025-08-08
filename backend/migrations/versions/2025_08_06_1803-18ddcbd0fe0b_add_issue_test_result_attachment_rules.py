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

"""Add issue test result attachment rules

Revision ID: 18ddcbd0fe0b
Revises: a23713521472
Create Date: 2025-08-06 18:03:03.281403+00:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "18ddcbd0fe0b"
down_revision = "a23713521472"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "issue_test_result_attachment_rule",
        sa.Column("issue_id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column(
            "families",
            postgresql.ARRAY(postgresql.ENUM(name="familyname", create_type=False)),
            nullable=False,
        ),
        sa.Column("environment_names", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("test_case_names", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("template_ids", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["issue_id"],
            ["issue.id"],
            name=op.f("issue_test_result_attachment_rule_issue_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id", name=op.f("issue_test_result_attachment_rule_pkey")
        ),
    )
    op.create_index(
        op.f("issue_test_result_attachment_rule_enabled_ix"),
        "issue_test_result_attachment_rule",
        ["enabled"],
        unique=False,
    )
    op.create_index(
        op.f("issue_test_result_attachment_rule_issue_id_ix"),
        "issue_test_result_attachment_rule",
        ["issue_id"],
        unique=False,
    )
    op.create_table(
        "issue_test_result_attachment_rule_execution_metadata",
        sa.Column("attachment_rule_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=200), nullable=False),
        sa.Column("value", sa.String(length=200), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["attachment_rule_id"],
            ["issue_test_result_attachment_rule.id"],
            name=op.f(
                "issue_test_result_attachment_rule_execution_metadata_attachment_rule_id_fkey"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "attachment_rule_id",
            "id",
            name=op.f("issue_test_result_attachment_rule_execution_metadata_pkey"),
        ),
    )
    op.add_column(
        "issue_test_result_attachment",
        sa.Column("attachment_rule_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        op.f("issue_test_result_attachment_attachment_rule_id_fkey"),
        "issue_test_result_attachment",
        "issue_test_result_attachment_rule",
        ["attachment_rule_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_column("issue_test_result_attachment", "attachment_rule_id")
    op.drop_table("issue_test_result_attachment_rule_execution_metadata")
    op.drop_table("issue_test_result_attachment_rule")
