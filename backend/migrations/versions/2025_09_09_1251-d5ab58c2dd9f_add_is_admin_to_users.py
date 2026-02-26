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

"""Add is_admin to users

Revision ID: d5ab58c2dd9f
Revises: 80d45097d01e
Create Date: 2025-09-09 12:51:22.567128+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d5ab58c2dd9f"
down_revision = "80d45097d01e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "app_user",
        sa.Column(
            "is_admin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
    )


def downgrade() -> None:
    op.drop_column("app_user", "is_admin")
