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

"""Add family reviewer team mapping table

Revision ID: 25e563acd30b
Revises: 3f6a99085db7
Create Date: 2025-11-05 10:26:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "25e563acd30b"
down_revision = "3f6a99085db7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create family_reviewer_team mapping table
    op.create_table(
        "family_reviewer_team",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column(
            "family",
            sa.Enum("snap", "deb", "charm", "image", name="familyname", create_type=False),
            nullable=False,
        ),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["team_id"], ["team.id"], name=op.f("family_reviewer_team_team_id_fkey")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("family_reviewer_team_pkey")),
        sa.UniqueConstraint("family", name=op.f("family_reviewer_team_family_key")),
    )
    op.create_index(
        op.f("family_reviewer_team_team_id_ix"),
        "family_reviewer_team",
        ["team_id"],
        unique=False,
    )
    
    # Add reviewer_team_id foreign key column to app_user
    op.add_column(
        "app_user",
        sa.Column("reviewer_team_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        op.f("app_user_reviewer_team_id_ix"),
        "app_user",
        ["reviewer_team_id"],
        unique=False,
    )
    op.create_foreign_key(
        op.f("app_user_reviewer_team_id_fkey"),
        "app_user",
        "team",
        ["reviewer_team_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("app_user_reviewer_team_id_fkey"), "app_user", type_="foreignkey"
    )
    op.drop_index(op.f("app_user_reviewer_team_id_ix"), table_name="app_user")
    op.drop_column("app_user", "reviewer_team_id")
    
    op.drop_index(
        op.f("family_reviewer_team_team_id_ix"), table_name="family_reviewer_team"
    )
    op.drop_table("family_reviewer_team")
