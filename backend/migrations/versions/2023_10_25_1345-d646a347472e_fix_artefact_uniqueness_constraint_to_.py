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

"""Fix artefact uniqueness constraint to exclude store

Revision ID: d646a347472e
Revises: 16043e3ffdd9
Create Date: 2023-10-25 13:45:11.298029+00:00

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "d646a347472e"
down_revision = "16043e3ffdd9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("unique_artefact", "artefact")
    op.create_unique_constraint(
        "unique_snap",
        "artefact",
        ["name", "version", "track"],
    )
    op.create_unique_constraint(
        "unique_deb",
        "artefact",
        ["name", "version", "series", "repo"],
    )


def downgrade() -> None:
    op.drop_constraint("unique_snap", "artefact")
    op.drop_constraint("unique_deb", "artefact")
    op.create_unique_constraint(
        "unique_artefact",
        "artefact",
        ["name", "version", "source"],
    )
