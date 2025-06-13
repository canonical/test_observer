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

"""Add artefact comment

Revision ID: 5e1ae326c8fc
Revises: b582856bd72e
Create Date: 2025-05-28 09:58:17.144197+00:00

"""

from alembic import op
import sqlalchemy as sa


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
