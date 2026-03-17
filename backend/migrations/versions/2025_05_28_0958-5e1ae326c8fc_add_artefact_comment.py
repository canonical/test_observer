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

"""Add artefact comment

Revision ID: 5e1ae326c8fc
Revises: b582856bd72e
Create Date: 2025-05-28 09:58:17.144197+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5e1ae326c8fc"
down_revision = "b582856bd72e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("artefact", sa.Column("comment", sa.String()))
    op.execute("UPDATE artefact SET comment = '' WHERE comment is NULL")
    op.alter_column("artefact", "comment", nullable=False)


def downgrade() -> None:
    op.drop_column("artefact", "comment")
