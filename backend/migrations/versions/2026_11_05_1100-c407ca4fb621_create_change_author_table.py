# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the License along with this program.
# If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Create change author table

Revision ID: c407ca4fb621
Revises: b7c2d9e4a1f0
Create Date: 2026-11-05 11:00:00.000000+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c407ca4fb621"
down_revision = "b7c2d9e4a1f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "change_author",
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("application_id", sa.Integer(), nullable=True),
        sa.Column("automation_name", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "num_nonnulls(user_id, application_id, automation_name) = 1",
            name="exactly_one_author",
        ),
        sa.CheckConstraint(
            "automation_name IS NULL OR btrim(automation_name) <> ''",
            name="automation_name_not_blank",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("change_author_pkey")),
        sa.UniqueConstraint("application_id", name=op.f("change_author_application_id_key")),
        sa.UniqueConstraint("automation_name", name=op.f("change_author_automation_name_key")),
        sa.UniqueConstraint("user_id", name=op.f("change_author_user_id_key")),
    )


def downgrade() -> None:
    op.drop_table("change_author")
