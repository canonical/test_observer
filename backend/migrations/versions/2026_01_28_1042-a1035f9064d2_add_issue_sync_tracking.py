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

"""Add issue sync tracking

Revision ID: a1035f9064d2
Revises: 5552667bf072
Create Date: 2026-01-28 10:42:17.613892+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1035f9064d2"
down_revision = "5552667bf072"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add last_synced_at column
    op.add_column("issue", sa.Column("last_synced_at", sa.DateTime(), nullable=True))

    # Add index for efficient querying
    op.create_index("idx_issue_status_last_synced", "issue", ["status", "last_synced_at"])


def downgrade() -> None:
    op.drop_index("idx_issue_status_last_synced", table_name="issue")
    op.drop_column("issue", "last_synced_at")
