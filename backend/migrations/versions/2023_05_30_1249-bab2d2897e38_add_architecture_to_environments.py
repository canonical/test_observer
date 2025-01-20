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


"""Add architecture to environments

Revision ID: bab2d2897e38
Revises: 183e6d6df6ff
Create Date: 2023-05-30 12:49:03.545470+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "bab2d2897e38"
down_revision = "183e6d6df6ff"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "environment", sa.Column("architecture", sa.String(length=100), nullable=False)
    )
    op.drop_index("ix_environment_name", table_name="environment")
    op.create_unique_constraint(
        "unique_environment", "environment", ["name", "architecture"]
    )


def downgrade() -> None:
    op.drop_constraint("unique_environment", "environment", type_="unique")
    op.create_index("ix_environment_name", "environment", ["name"], unique=False)
    op.drop_column("environment", "architecture")
