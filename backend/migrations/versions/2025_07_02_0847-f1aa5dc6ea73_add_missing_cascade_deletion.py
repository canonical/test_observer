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

"""Add missing cascade deletion for reruns

Revision ID: f1aa5dc6ea73
Revises: 87f9e68e61a7
Create Date: 2025-07-02 08:47:22.068336+00:00

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "f1aa5dc6ea73"
down_revision = "87f9e68e61a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "test_execution_rerun_request_test_execution_id_fkey",
        "test_execution_rerun_request",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("test_execution_rerun_request_test_execution_id_fkey"),
        "test_execution_rerun_request",
        "test_execution",
        ["test_execution_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("test_execution_rerun_request_test_execution_id_fkey"),
        "test_execution_rerun_request",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "test_execution_rerun_request_test_execution_id_fkey",
        "test_execution_rerun_request",
        "test_execution",
        ["test_execution_id"],
        ["id"],
    )
