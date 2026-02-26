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

"""add test_execution_relevant_links

Revision ID: 87f9e68e61a7
Revises: b582856bd72e
Create Date: 2025-05-29 10:31:17.328173+00:00

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "87f9e68e61a7"
down_revision = "5e1ae326c8fc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "test_execution_relevant_link",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("test_execution_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["test_execution_id"],
            ["test_execution.id"],
            name=op.f("test_execution_relevant_link_test_execution_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("test_execution_relevant_link_pkey")),
    )
    op.create_index(
        op.f("test_execution_relevant_link_test_execution_id_ix"),
        "test_execution_relevant_link",
        ["test_execution_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("test_execution_relevant_link_test_execution_id_ix"),
        table_name="test_execution_relevant_link",
    )
    op.drop_table("test_execution_relevant_link")
