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

"""Backfill artefact.attributes from legacy bundled build fields

Second (still non-destructive) step of moving solution-specific data into the
generic ``attributes`` field. It copies existing ``bundled_builds_hash`` and
``artefact_bundled_builds_association`` data into ``attributes`` for rows that
predate the write-both code.

The legacy ``bundled_builds_hash`` column and
``artefact_bundled_builds_association`` table are intentionally left in place so
that code running against the old schema keeps working during a rolling
upgrade. Dropping them is the destructive (contract) step in a later,
separately deployed migration.

Revision ID: d315c1f212b9
Revises: 6e262c3c6c8f
Create Date: 2026-08-17 17:24:00.000000+00:00

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "d315c1f212b9"
down_revision = "6e262c3c6c8f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    _copy_bundled_builds_to_attributes()


def downgrade() -> None:
    # Data-only backfill. The ``attributes`` column itself is dropped by the
    # downgrade of the preceding migration, so there is nothing to reverse here.
    pass


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
