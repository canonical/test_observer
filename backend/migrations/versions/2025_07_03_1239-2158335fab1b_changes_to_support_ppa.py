# Copyright (C) 2025 Canonical Ltd.
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

"""Changes to support ppa

Revision ID: 2158335fab1b
Revises: f1aa5dc6ea73
Create Date: 2025-07-03 12:39:07.797701+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2158335fab1b"
down_revision = "f1aa5dc6ea73"
branch_labels = None
depends_on = None


def upgrade() -> None:
    _add_source_column()
    _change_unique_constraints()
    _change_stage_type()


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


def _change_stage_type() -> None:
    op.alter_column("artefact", "stage", type_=sa.VARCHAR(100))
    op.execute("DROP TYPE stagename")


def downgrade() -> None:
    _revert_stage_type()
    op.execute("DELETE FROM artefact WHERE source != ''")
    _revert_unique_constraints()
    op.drop_column("artefact", "source")


def _revert_unique_constraints() -> None:
    op.drop_index("unique_deb", "artefact")

    op.create_index(
        "unique_deb",
        "artefact",
        ["name", "version", "series", "repo"],
        unique=True,
        postgresql_where=sa.text("family = 'deb'"),
    )


def _revert_stage_type() -> None:
    op.execute(
        "DELETE FROM artefact WHERE stage NOT IN "
        "('edge', 'beta', 'candidate', 'stable', 'proposed', 'updates')"
    )
    op.execute(
        "CREATE TYPE stagename AS "
        "ENUM('edge', 'beta', 'candidate', 'stable', 'proposed', 'updates')"
    )
    op.execute(
        "ALTER TABLE artefact ALTER COLUMN stage TYPE "
        "stagename USING stage::text::stagename"
    )
