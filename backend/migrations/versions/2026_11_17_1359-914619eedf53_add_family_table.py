# Copyright 2026 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Add family table

Revision ID: 914619eedf53
Revises: d28bd2fc909d
Create Date: 2026-11-17 13:59:50.787951+00:00

"""

from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision = "914619eedf53"
down_revision = "d28bd2fc909d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    family = op.create_table(
        "family",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("name", name=op.f("family_pkey")),
    )
    timestamp = datetime.now()
    op.bulk_insert(
        family,
        [
            {"name": name, "created_at": timestamp, "updated_at": timestamp}
            for name in ("snap", "deb", "charm", "image", "solution")
        ],
    )


def downgrade() -> None:
    op.drop_table("family")
