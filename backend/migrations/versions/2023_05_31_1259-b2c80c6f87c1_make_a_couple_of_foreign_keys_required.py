# Copyright 2023 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Make a couple of foreign keys required

Revision ID: b2c80c6f87c1
Revises: bab2d2897e38
Create Date: 2023-05-31 12:59:40.263937+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b2c80c6f87c1"
down_revision = "bab2d2897e38"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("artefact", "stage_id", existing_type=sa.INTEGER(), nullable=False)
    op.alter_column("stage", "family_id", existing_type=sa.INTEGER(), nullable=False)


def downgrade() -> None:
    op.alter_column("stage", "family_id", existing_type=sa.INTEGER(), nullable=True)
    op.alter_column("artefact", "stage_id", existing_type=sa.INTEGER(), nullable=True)
