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

"""Add test case and environment indexes

Revision ID: 0d584fc6add7
Revises: 84dd9c0ed8f8
Create Date: 2025-09-16 11:21:48.114547+00:00

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "0d584fc6add7"
down_revision = "84dd9c0ed8f8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Environment index for ORDER BY name queries
    op.create_index("idx_environment_name", "environment", ["name"])

    # Test case composite index - this covers both SELECT and ORDER BY
    op.create_index("idx_test_case_name_template", "test_case", ["name", "template_id"])


def downgrade() -> None:
    op.drop_index("idx_test_case_name_template", "test_case")
    op.drop_index("idx_environment_name", "environment")
