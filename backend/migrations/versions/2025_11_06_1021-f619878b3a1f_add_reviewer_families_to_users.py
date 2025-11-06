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

"""Add reviewer_families to users and remove is_reviewer

Revision ID: f619878b3a1f
Revises: 3f6a99085db7
Create Date: 2025-11-06 10:21:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "f619878b3a1f"
down_revision = "3f6a99085db7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add reviewer_families array column to app_user
    op.add_column(
        "app_user",
        sa.Column(
            "reviewer_families",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
    )
    
    # Migrate existing is_reviewer=True users to have snap and deb families
    op.execute("""
        UPDATE app_user 
        SET reviewer_families = ARRAY['snap', 'deb']::varchar[]
        WHERE is_reviewer = true
    """)
    
    # Drop the is_reviewer column
    op.drop_column("app_user", "is_reviewer")


def downgrade() -> None:
    # Re-add is_reviewer column
    op.add_column(
        "app_user",
        sa.Column(
            "is_reviewer",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
    )
    
    # Set is_reviewer to true for users with any reviewer_families
    op.execute("""
        UPDATE app_user 
        SET is_reviewer = true
        WHERE array_length(reviewer_families, 1) > 0
    """)
    
    # Drop reviewer_families column
    op.drop_column("app_user", "reviewer_families")
