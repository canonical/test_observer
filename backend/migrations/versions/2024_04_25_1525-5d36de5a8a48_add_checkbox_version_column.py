# Copyright (C) 2023 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Add checkbox version column

Revision ID: 5d36de5a8a48
Revises: 624a270a03dc
Create Date: 2024-04-25 15:25:33.149465+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5d36de5a8a48"
down_revision = "624a270a03dc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "test_execution",
        sa.Column("checkbox_version", sa.String(length=200), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("test_execution", "checkbox_version")
