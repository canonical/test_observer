# Copyright (C) 2023-2025 Canonical Ltd.
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


"""disallow multiple artefact builds with null revision

Revision ID: 158244992900
Revises: b33ee8dd41b1
Create Date: 2023-07-11 11:48:49.777726+00:00

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "158244992900"
down_revision = "6a80dad01d24"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "unique_artefact_build_null_revision",
        "artefact_build",
        ["artefact_id", "architecture"],
        unique=True,
        postgresql_where=("revision IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "unique_artefact_build_null_revision",
        "artefact_build",
    )
