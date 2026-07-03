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

"""Add index on test_execution updated_at

Revision ID: eba1d1c92dba
Revises: 624b22905ce2
Create Date: 2026-07-02 16:19:59.487151+00:00

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "eba1d1c92dba"
down_revision = "624b22905ce2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(op.f("test_execution_updated_at_ix"), "test_execution", ["updated_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("test_execution_updated_at_ix"), table_name="test_execution")
