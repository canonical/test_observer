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


"""Drop Artefact source field

Revision ID: 49221114815a
Revises: d646a347472e
Create Date: 2023-10-26 07:55:27.449425+00:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "49221114815a"
down_revision = "d646a347472e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("artefact", "source")


def downgrade() -> None:
    op.add_column(
        "artefact",
        sa.Column("source", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    artefact_table = sa.table(
        "artefact",
        sa.column("id", sa.Integer()),
        sa.column("track", sa.String()),
        sa.column("store", sa.String()),
        sa.column("series", sa.String()),
        sa.column("repo", sa.String()),
        sa.column("source", postgresql.JSONB(astext_type=sa.Text())),
    )

    conn = op.get_bind()
    for artefact in conn.execute(sa.select(artefact_table)):
        source = {
            k: getattr(artefact, k)
            for k in ["track", "store", "series", "repo"]
            if getattr(artefact, k) is not None
        }

        conn.execute(
            sa.update(artefact_table)
            .where(artefact_table.c.id == artefact.id)
            .values(source=source)
        )

    op.alter_column("artefact", "source", nullable=False)
