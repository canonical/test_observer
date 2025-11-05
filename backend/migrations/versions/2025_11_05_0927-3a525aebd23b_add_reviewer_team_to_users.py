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

"""Add reviewer_team to users

Revision ID: 3a525aebd23b
Revises: 3f6a99085db7
Create Date: 2025-11-05 09:27:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3a525aebd23b"
down_revision = "3f6a99085db7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the enum type first
    op.execute("CREATE TYPE reviewerteam AS ENUM ('sqa', 'cert')")
    
    # Then add the column
    op.add_column(
        "app_user",
        sa.Column(
            "reviewer_team",
            sa.Enum("sqa", "cert", name="reviewerteam"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("app_user", "reviewer_team")
    op.execute("DROP TYPE reviewerteam")
