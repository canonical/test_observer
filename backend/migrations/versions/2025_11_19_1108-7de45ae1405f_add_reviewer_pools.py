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

"""Create reviewer pool tables

Revision ID: 7de45ae1405f
Revises: 3f6a99085db7
Create Date: 2025-11-19 14:00:00.000000+00:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "7de45ae1405f"
down_revision = "3f6a99085db7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("pool_members_user_id_ix", table_name="pool_members", if_exists=True)
    op.drop_index("pool_members_pool_id_ix", table_name="pool_members", if_exists=True)
    op.drop_table("pool_members", if_exists=True)
    op.drop_table("reviewer_pool", if_exists=True)

    # Create reviewer_pool table (fresh)
    op.create_table(
        "reviewer_pool",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "families",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create pool_members table
    op.create_table(
        "pool_members",
        sa.Column("pool_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["pool_id"],
            ["reviewer_pool.id"],
            name="pool_members_pool_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("pool_id", "user_id"),
    )

    # Create indexes
    op.create_index(
        "pool_members_pool_id_ix",
        "pool_members",
        ["pool_id"],
        unique=False,
    )
    op.create_index(
        "pool_members_user_id_ix",
        "pool_members",
        ["user_id"],
        unique=False,
    )

    # Insert default pools
    op.execute(
        "INSERT INTO reviewer_pool (name, families, created_at, updated_at) "
        "VALUES ('cert', ARRAY['snap', 'deb', 'image'], NOW(), NOW())"
    )
    op.execute(
        "INSERT INTO reviewer_pool (name, families, created_at, updated_at) "
        "VALUES ('sqa', ARRAY['charm'], NOW(), NOW())"
    )


def downgrade() -> None:
    # Drop pool_members first (has foreign keys)
    op.drop_index("pool_members_user_id_ix", table_name="pool_members")
    op.drop_index("pool_members_pool_id_ix", table_name="pool_members")
    op.drop_table("pool_members")

    # Then drop reviewer_pool
    op.drop_table("reviewer_pool")
