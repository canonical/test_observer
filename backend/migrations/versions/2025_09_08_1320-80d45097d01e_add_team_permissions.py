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

"""Add team permissions

Revision ID: 80d45097d01e
Revises: f496f12b66b8
Create Date: 2025-09-08 13:20:45.727848+00:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "80d45097d01e"
down_revision = "f496f12b66b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "team", sa.Column("permissions", postgresql.ARRAY(sa.String()), nullable=False)
    )


def downgrade() -> None:
    op.drop_column("team", "permissions")
