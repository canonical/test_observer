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


"""Update artefact unique constraint

Revision ID: 2be627e68efd
Revises: 121edad6b53f
Create Date: 2025-01-14 09:34:28.190863+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2be627e68efd"
down_revision = "121edad6b53f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "unique_charm",
        "artefact",
        ["name", "version", "track"],
        unique=True,
        postgresql_where=sa.text("family = 'charm'"),
    )
    op.create_index(
        "unique_image",
        "artefact",
        ["sha256"],
        unique=True,
        postgresql_where=sa.text("family = 'image'"),
    )

    op.drop_index("unique_snap", "artefact")
    op.create_index(
        "unique_snap",
        "artefact",
        ["name", "version", "track"],
        unique=True,
        postgresql_where=sa.text("family = 'snap'"),
    )

    op.drop_index("unique_deb", "artefact")
    op.create_index(
        "unique_deb",
        "artefact",
        ["name", "version", "series", "repo"],
        unique=True,
        postgresql_where=sa.text("family = 'deb'"),
    )


def downgrade() -> None:
    op.drop_index("unique_deb", "artefact")
    op.create_index(
        "unique_deb",
        "artefact",
        ["name", "version", "series", "repo"],
        unique=True,
        postgresql_where=sa.text("series != '' AND repo != ''"),
    )

    op.drop_index("unique_snap", "artefact")
    op.create_index(
        "unique_snap",
        "artefact",
        ["name", "version", "track"],
        unique=True,
        postgresql_where=sa.text("track != ''"),
    )

    op.drop_index("unique_image", table_name="artefact")
    op.drop_index("unique_charm", table_name="artefact")
