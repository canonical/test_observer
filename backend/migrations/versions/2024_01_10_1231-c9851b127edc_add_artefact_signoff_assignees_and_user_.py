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

"""Add artefact signoff assignees and user model

Revision ID: c9851b127edc
Revises: f7b452b19e46
Create Date: 2024-01-10 12:31:07.508443+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c9851b127edc"
down_revision = "f7b452b19e46"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("launchpad_email", sa.String(), nullable=False),
        sa.Column("launchpad_handle", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("user_pkey")),
        sa.UniqueConstraint("launchpad_email", name=op.f("user_launchpad_email_key")),
    )
    op.add_column("artefact", sa.Column("assignee_id", sa.Integer(), nullable=True))
    op.create_foreign_key(op.f("artefact_assignee_id_fkey"), "artefact", "user", ["assignee_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint(op.f("artefact_assignee_id_fkey"), "artefact", type_="foreignkey")
    op.drop_column("artefact", "assignee_id")
    op.drop_table("user")
