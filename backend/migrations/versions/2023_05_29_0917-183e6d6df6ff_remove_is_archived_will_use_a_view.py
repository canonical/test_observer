# Copyright 2023 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Remove is_archived, will use a view

Revision ID: 183e6d6df6ff
Revises: 12383cab7248
Create Date: 2023-05-29 09:17:37.129881+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "183e6d6df6ff"
down_revision = "12383cab7248"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("artefact", "is_archived")


def downgrade() -> None:
    op.add_column(
        "artefact",
        sa.Column("is_archived", sa.BOOLEAN(), autoincrement=False, nullable=False),
    )
