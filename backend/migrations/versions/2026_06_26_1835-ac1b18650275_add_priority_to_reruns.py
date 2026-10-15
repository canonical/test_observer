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

"""Add priority to reruns

Revision ID: ac1b18650275
Revises: 236cc88a9a64
Create Date: 2026-06-26 18:35:32.947482+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ac1b18650275"
down_revision = "236cc88a9a64"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "test_execution_rerun_request",
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(
        "idx_rerun_request_priority_created_at",
        "test_execution_rerun_request",
        [sa.text("priority DESC"), sa.text("created_at ASC")],
    )


def downgrade() -> None:
    op.drop_index("idx_rerun_request_priority_created_at", table_name="test_execution_rerun_request")
    op.drop_column("test_execution_rerun_request", "priority")
