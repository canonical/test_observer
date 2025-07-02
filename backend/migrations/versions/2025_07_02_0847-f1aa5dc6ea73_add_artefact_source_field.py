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

"""Add artefact source field

Revision ID: f1aa5dc6ea73
Revises: 87f9e68e61a7
Create Date: 2025-07-02 08:47:22.068336+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f1aa5dc6ea73"
down_revision = "87f9e68e61a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    _add_source_column()
    _change_unique_constraints()


def downgrade() -> None:
    op.execute("DELETE FROM artefact WHERE source != ''")
    _revert_unique_constraints()
    op.drop_column("artefact", "source")


def _add_source_column() -> None:
    op.add_column("artefact", sa.Column("source", sa.String(length=200)))
    op.execute("UPDATE artefact SET source = '' WHERE source is NULL")
    op.alter_column("artefact", "source", nullable=False)


def _change_unique_constraints() -> None:
    op.drop_index("unique_deb", "artefact")

    op.create_index(
        "unique_deb",
        "artefact",
        ["name", "version", "series", "repo", "source"],
        unique=True,
        postgresql_where=sa.text("family = 'deb'"),
    )


def _revert_unique_constraints() -> None:
    op.drop_index("unique_deb", "artefact")

    op.create_index(
        "unique_deb",
        "artefact",
        ["name", "version", "series", "repo"],
        unique=True,
        postgresql_where=sa.text("family = 'deb'"),
    )
