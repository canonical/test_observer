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

"""Add index to TestResult created_at

Revision ID: 3f6a99085db7
Revises: 438c847d57eb
Create Date: 2025-10-16 17:19:24.401782+00:00

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "3f6a99085db7"
down_revision = "438c847d57eb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        op.f("test_result_created_at_ix"), "test_result", ["created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("test_result_created_at_ix"), table_name="test_result")
