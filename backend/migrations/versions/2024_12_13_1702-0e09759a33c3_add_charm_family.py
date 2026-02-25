# Copyright 2024 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Add charm family

Revision ID: 0e09759a33c3
Revises: 4c2e5946358c
Create Date: 2024-12-13 17:02:14.136283+00:00

"""

import sqlalchemy as sa
from alembic import op

from test_observer.data_access.models_enums import FamilyName

new_families = {
    FamilyName.charm: ["edge", "beta", "candidate", "stable"],
}


# revision identifiers, used by Alembic.
revision = "0e09759a33c3"
down_revision = "4c2e5946358c"
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

    for family_name, stage_names in new_families.items():
        # Create family
        (inserted_family,) = conn.execute(
            sa.insert(family_table)
            .values(
                name=family_name,
                created_at=sa.func.now(),
                updated_at=sa.func.now(),
            )
            .returning(family_table.c.id)
        )

        # Add stages
        stage_position = 10
        for stage_name in stage_names:
            conn.execute(
                sa.insert(stage_table).values(
                    name=stage_name,
                    family_id=inserted_family.id,
                    position=stage_position,
                    created_at=sa.func.now(),
                    updated_at=sa.func.now(),
                )
            )
            stage_position += 10


def downgrade() -> None:
    conn = op.get_bind()

    family_table = sa.table(
        "family",
        sa.column("id", sa.Integer()),
        sa.column("name", sa.String()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )

    # Delete each family, stage deletes on cascade
    for family_name in new_families:
        conn.execute(sa.delete(family_table).where(family_table.c.name == family_name))
