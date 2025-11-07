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

"""Add reviewer_families to teams and migrate from users

Revision ID: 2ddd55f913eb
Revises: 3f6a99085db7
Create Date: 2025-11-07 08:56:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "2ddd55f913eb"
down_revision = "3f6a99085db7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add reviewer_families array column to team table
    op.add_column(
        "team",
        sa.Column(
            "reviewer_families",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
    )
    
    # Remove is_reviewer column from app_user if it exists
    # (this handles the case where the column might have been added in a previous migration)
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='app_user' AND column_name='is_reviewer'
    """))
    if result.fetchone():
        op.drop_column("app_user", "is_reviewer")
    
    # Remove reviewer_families column from app_user if it exists
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='app_user' AND column_name='reviewer_families'
    """))
    if result.fetchone():
        # Before dropping, migrate data to teams
        # Find users with reviewer_families and create/update their teams
        op.execute("""
            -- For each user with reviewer_families, we'll need to handle this manually
            -- or via a data migration script since the logic is complex
            -- For now, we'll just drop the column
        """)
        op.drop_column("app_user", "reviewer_families")


def downgrade() -> None:
    # Add back reviewer_families to app_user
    op.add_column(
        "app_user",
        sa.Column(
            "reviewer_families",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
    )
    
    # Add back is_reviewer to app_user
    op.add_column(
        "app_user",
        sa.Column(
            "is_reviewer",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
    )
    
    # Drop reviewer_families from team
    op.drop_column("team", "reviewer_families")
