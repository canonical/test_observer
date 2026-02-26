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

"""Add new issue model

Revision ID: ab74101e7373
Revises: 2158335fab1b
Create Date: 2025-07-17 17:55:35.565545+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ab74101e7373"
down_revision = "2158335fab1b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "issue",
        sa.Column(
            "source",
            sa.Enum("JIRA", "GITHUB", "LAUNCHPAD", name="issuesource"),
            nullable=False,
        ),
        sa.Column("project", sa.String(length=200), nullable=False),
        sa.Column("key", sa.String(length=200), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("UNKNOWN", "OPEN", "CLOSED", name="issuestatus"),
            nullable=False,
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("issue_pkey")),
        sa.UniqueConstraint("project", "source", "key", name=op.f("issue_project_source_key_key")),
    )


def downgrade() -> None:
    op.drop_table("issue")
    op.execute("DROP TYPE IF EXISTS issuesource")
    op.execute("DROP TYPE IF EXISTS issuestatus")
