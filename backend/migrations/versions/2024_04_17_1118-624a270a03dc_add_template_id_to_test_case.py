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


"""Add template id to test case

Revision ID: 624a270a03dc
Revises: ae281506fe32
Create Date: 2024-04-17 11:18:27.430695+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "624a270a03dc"
down_revision = "ae281506fe32"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "test_case",
        sa.Column("template_id", sa.String(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("test_case", "template_id")
