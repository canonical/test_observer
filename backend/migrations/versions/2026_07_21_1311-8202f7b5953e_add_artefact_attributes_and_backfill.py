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

"""Add artefact.attributes and backfill bundled builds into it

This is the non-destructive (expand) half of adding the ``attributes`` column
to artefacts and removing solution-specific fields.

It only adds the new column and copies existing data into it, leaving
``bundled_builds_hash`` and ``artefact_bundled_builds_association`` in place
so that code running against the old schema keeps working during a rolling
upgrade.

The destructive (contract) half - swapping the ``unique_solution`` index and
dropping the old column/table - lives in a separate, later migration that must
be released only after this one has been fully rolled out.

Revision ID: 8202f7b5953e
Revises: eba1d1c92dba
Create Date: 2026-07-21 13:11:39.128081+00:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "8202f7b5953e"
down_revision = "eba1d1c92dba"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("artefact", sa.Column("attributes", postgresql.JSONB(), server_default="{}", nullable=False))
    _copy_bundled_builds_to_attributes()


def downgrade() -> None:
    op.drop_column("artefact", "attributes")


def _copy_bundled_builds_to_attributes() -> None:
    op.execute(
        """
        UPDATE artefact AS a
        SET attributes = a.attributes
            || jsonb_strip_nulls(
                 jsonb_build_object('bundled_builds_hash', a.bundled_builds_hash)
               )
            || COALESCE(
                 (
                     SELECT jsonb_build_object(
                              'bundled_builds',
                              jsonb_agg(assoc.artefact_build_id ORDER BY assoc.artefact_build_id)
                            )
                     FROM artefact_bundled_builds_association assoc
                     WHERE assoc.artefact_id = a.id
                     HAVING count(*) > 0
                 ),
                 '{}'::jsonb
               )
        WHERE a.bundled_builds_hash IS NOT NULL
           OR EXISTS (
               SELECT 1
               FROM artefact_bundled_builds_association assoc
               WHERE assoc.artefact_id = a.id
           )
        """
    )
