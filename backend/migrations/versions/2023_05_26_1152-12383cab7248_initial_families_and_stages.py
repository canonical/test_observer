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


"""Initial families and stages

Revision ID: 12383cab7248
Revises: 7a9069d2ab59
Create Date: 2023-05-26 11:52:18.703471+00:00

"""

import sqlalchemy as sa
from alembic import op

from test_observer.data_access.models_enums import FamilyName

initial_families_and_stages = {
    FamilyName.snap: ["edge", "beta", "candidate", "stable"],
    FamilyName.deb: ["proposed", "updates"],
}

# revision identifiers, used by Alembic.
revision = "12383cab7248"
down_revision = "7a9069d2ab59"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    family_table = sa.table(
        "family",
        sa.column("id", sa.Integer()),
        sa.column("name", sa.String()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )
    stage_table = sa.table(
        "stage",
        sa.column("name", sa.String()),
        sa.column("family_id", sa.Integer()),
        sa.column("position", sa.Integer()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )

    for family in initial_families_and_stages:
        (inserted_family,) = conn.execute(
            sa.insert(family_table)
            .values(
                name=family.value,
                created_at=sa.func.now(),
                updated_at=sa.func.now(),
            )
            .returning(family_table.c.id)
        )
        stage_position = 10
        for stage in initial_families_and_stages[family]:
            conn.execute(
                sa.insert(stage_table).values(
                    name=stage,
                    family_id=inserted_family.id,
                    position=stage_position,
                    created_at=sa.func.now(),
                    updated_at=sa.func.now(),
                )
            )
            stage_position += 10


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.delete(sa.table("stage")))
    conn.execute(sa.delete(sa.table("family")))
