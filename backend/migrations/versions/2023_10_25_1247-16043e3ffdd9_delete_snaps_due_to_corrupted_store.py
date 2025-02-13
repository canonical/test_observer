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


"""Delete snaps due to corrupted store

Revision ID: 16043e3ffdd9
Revises: 0d23bbbe9ec8
Create Date: 2023-10-25 12:47:01.958805+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "16043e3ffdd9"
down_revision = "0d23bbbe9ec8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This is a distructive migration it will remove all snaps from the database.
    # The reason is that store should not be part of the unique constraint,
    # and merging the fragmented snap artefacts will be challenging. Especially
    # given that we don't know what the appropriate store should be.

    artefact_table = sa.table("artefact", sa.column("stage_id"))
    stage_table = sa.table("stage", sa.column("id"), sa.column("family_id"))
    family_table = sa.table("family", sa.column("id"), sa.column("name"))

    conn = op.get_bind()

    delete_stmt = (
        sa.delete(artefact_table)
        .where(artefact_table.c.stage_id == stage_table.c.id)
        .where(stage_table.c.family_id == family_table.c.id)
        .where(family_table.c.name == "snap")
    )

    conn.execute(delete_stmt)


def downgrade() -> None:
    pass
