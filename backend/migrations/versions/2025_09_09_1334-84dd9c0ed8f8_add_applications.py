# Copyright 2025 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Add applications

Revision ID: 84dd9c0ed8f8
Revises: d5ab58c2dd9f
Create Date: 2025-09-09 13:34:20.370764+00:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "84dd9c0ed8f8"
down_revision = "d5ab58c2dd9f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "application",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("permissions", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("api_key", sa.String(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("application_pkey")),
        sa.UniqueConstraint("name", name=op.f("application_name_key")),
        sa.UniqueConstraint("api_key", name=op.f("application_api_key_key")),
    )


def downgrade() -> None:
    op.drop_table("application")
