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

"""Add artefact.attributes

This is the first (expand) step of adding a generic ``attributes`` field to
artefacts. It only adds the new column with an empty-object default so that
code running against the old schema keeps working during a rolling upgrade.

Backfilling existing data into ``attributes`` and switching the code to read
from it happen in later, separately deployed migrations.

Revision ID: 6e262c3c6c8f
Revises: eba1d1c92dba
Create Date: 2026-08-17 17:23:00.000000+00:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "6e262c3c6c8f"
down_revision = "eba1d1c92dba"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("artefact", sa.Column("attributes", postgresql.JSONB(), server_default="{}", nullable=False))


def downgrade() -> None:
    op.drop_column("artefact", "attributes")
