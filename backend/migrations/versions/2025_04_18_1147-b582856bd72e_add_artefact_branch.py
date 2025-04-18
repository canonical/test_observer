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

"""Add artefact branch

Revision ID: b582856bd72e
Revises: 6a726050c944
Create Date: 2025-04-18 11:47:29.933275+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b582856bd72e"
down_revision = "6a726050c944"
branch_labels = None
depends_on = None


def upgrade() -> None:
    _add_branch_column()
    _change_unique_constraints()


def downgrade() -> None:
    op.execute("DELETE FROM artefact WHERE branch != ''")
    _revert_unique_constraints()
    op.drop_column("artefact", "branch")


def _add_branch_column():
    op.add_column("artefact", sa.Column("branch", sa.String(length=200)))
    op.execute("UPDATE artefact SET branch = '' WHERE branch is NULL")
    op.alter_column("artefact", "branch", nullable=False)


def _change_unique_constraints():
    op.drop_index("unique_snap", "artefact")
    op.drop_index("unique_charm", "artefact")

    op.create_index(
        "unique_snap",
        "artefact",
        ["name", "version", "track", "branch"],
        unique=True,
        postgresql_where=sa.text("family = 'snap'"),
    )
    op.create_index(
        "unique_charm",
        "artefact",
        ["name", "version", "track", "branch"],
        unique=True,
        postgresql_where=sa.text("family = 'charm'"),
    )


def _revert_unique_constraints():
    op.drop_index("unique_snap", "artefact")
    op.drop_index("unique_charm", "artefact")

    op.create_index(
        "unique_snap",
        "artefact",
        ["name", "version", "track"],
        unique=True,
        postgresql_where=sa.text("family = 'snap'"),
    )
    op.create_index(
        "unique_charm",
        "artefact",
        ["name", "version", "track"],
        unique=True,
        postgresql_where=sa.text("family = 'charm'"),
    )
    # ### end Alembic commands ###
