# Copyright 2026 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Drop family enum type

Revision ID: c39a5eedb008
Revises: ad7acb807c63
Create Date: 2026-11-19 14:38:04.037962+00:00

"""

from alembic import op
from sqlalchemy.dialects import postgresql

revision = "c39a5eedb008"
down_revision = "ad7acb807c63"
branch_labels = None
depends_on = None

family_enum = postgresql.ENUM("snap", "deb", "charm", "image", "solution", name="familyname")


def upgrade() -> None:
    family_enum.drop(op.get_bind())


def downgrade() -> None:
    family_enum.create(op.get_bind())
