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

"""Make environment issues URL nullable

Revision ID: 9d7eed94a543
Revises: 505b96fd7731
Create Date: 2024-09-23 08:40:44.972779+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9d7eed94a543"
down_revision = "505b96fd7731"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "environment_issue", "url", existing_type=sa.VARCHAR(), nullable=True
    )


def downgrade() -> None:
    op.alter_column(
        "environment_issue", "url", existing_type=sa.VARCHAR(), nullable=False
    )
