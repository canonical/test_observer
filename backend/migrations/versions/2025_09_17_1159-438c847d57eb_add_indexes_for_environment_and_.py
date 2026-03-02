# Copyright 2025 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Add indexes for Environment and TestCase tables

Revision ID: 438c847d57eb
Revises: 84dd9c0ed8f8
Create Date: 2025-09-17 11:59:04.874309+00:00

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "438c847d57eb"
down_revision = "84dd9c0ed8f8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add indexes for Environment table to improve query performance
    op.create_index(
        op.f("environment_name_ix"),
        "environment",
        ["name"],
        unique=False,
    )
    op.create_index(
        op.f("environment_architecture_ix"),
        "environment",
        ["architecture"],
        unique=False,
    )

    # Add indexes for TestCase table to improve query performance
    op.create_index(
        op.f("test_case_category_ix"),
        "test_case",
        ["category"],
        unique=False,
    )
    op.create_index(
        op.f("test_case_template_id_ix"),
        "test_case",
        ["template_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("test_case_template_id_ix"), table_name="test_case")
    op.drop_index(op.f("test_case_category_ix"), table_name="test_case")
    op.drop_index(op.f("environment_architecture_ix"), table_name="environment")
    op.drop_index(op.f("environment_name_ix"), table_name="environment")
