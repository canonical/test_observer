# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Add expected environments to artefacts

Revision ID: b7c2d9e4a1f0
Revises: b2db87f4400c
Create Date: 2026-10-08 09:00:00.000000+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b7c2d9e4a1f0"
down_revision = "b2db87f4400c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "artefact_expected_environments_association",
        sa.Column("artefact_id", sa.Integer(), nullable=False),
        sa.Column("environment_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["artefact_id"],
            ["artefact.id"],
            name=op.f("artefact_expected_environments_association_artefact_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["environment_id"],
            ["environment.id"],
            name=op.f("artefact_expected_environments_association_environment_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "artefact_id", "environment_id", name=op.f("artefact_expected_environments_association_pkey")
        ),
    )


def downgrade() -> None:
    op.drop_table("artefact_expected_environments_association")
