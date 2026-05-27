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

"""Remove risk from Artefact

Revision ID: 236cc88a9a64
Revises: 717189ad8f3f
Create Date: 2026-05-26 10:58:42.183696+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "236cc88a9a64"
down_revision = "717189ad8f3f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("unique_solution", table_name="artefact", postgresql_where="(family = 'solution'::familyname)")
    op.create_index(
        "unique_solution",
        "artefact",
        ["name", "source", "version", "track", "stage", "bundled_builds_hash"],
        unique=True,
        postgresql_where=sa.text("family = 'solution'"),
    )
    # write the risk value to stage if stage is not set (empty)
    op.execute("""UPDATE artefact SET stage = risk WHERE stage = ''""")
    op.drop_column("artefact", "risk")


def downgrade() -> None:
    op.add_column(
        "artefact",
        sa.Column(
            "risk",
            sa.VARCHAR(length=200),
            server_default=sa.text("''::character varying"),
            autoincrement=False,
            nullable=False,
        ),
    )
    # write the stage value to risk
    op.execute("""UPDATE artefact SET risk = stage""")
    op.drop_index("unique_solution", table_name="artefact", postgresql_where=sa.text("family = 'solution'"))
    op.create_index(
        "unique_solution",
        "artefact",
        ["name", "source", "version", "track", "risk", "bundled_builds_hash"],
        unique=True,
        postgresql_where="(family = 'solution'::familyname)",
    )
