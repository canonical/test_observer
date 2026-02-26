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

"""Add test plan to test execution

Revision ID: 4c2e5946358c
Revises: b3b376fb6353
Create Date: 2024-12-05 10:00:53.848151+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4c2e5946358c"
down_revision = "b3b376fb6353"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "test_execution",
        sa.Column(
            "test_plan",
            sa.String(length=200),
            nullable=True,
        ),
    )

    op.execute("UPDATE test_execution SET test_plan = ''")

    op.execute("ALTER TABLE test_execution ALTER COLUMN test_plan SET NOT NULL")


def downgrade() -> None:
    op.drop_column("test_execution", "test_plan")
