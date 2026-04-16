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

"""Add all Artefact attributes to ArtefactMatchingRules

Revision ID: d9c144615947
Revises: f0847700d32e
Create Date: 2026-04-15 22:58:28.960881+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d9c144615947"
down_revision = "f0847700d32e"
branch_labels = None
depends_on = None


PREVIOUS_CONSTRAINT_NAME = "artefact_matching_rule_name_family_stage_track_branch_key"
NEW_CONSTRAINT_NAME = "artefact_matching_rule_fields_from_artefact"

# Update this if your association table has a different name
ASSOCIATION_TABLE_NAME = "artefact_matching_rule_team_association"


def upgrade() -> None:
    op.add_column(
        "artefact_matching_rule", sa.Column("store", sa.String(length=200), server_default="", nullable=False)
    )
    op.add_column(
        "artefact_matching_rule", sa.Column("series", sa.String(length=200), server_default="", nullable=False)
    )
    op.add_column("artefact_matching_rule", sa.Column("os", sa.String(length=200), server_default="", nullable=False))
    op.add_column(
        "artefact_matching_rule", sa.Column("release", sa.String(length=200), server_default="", nullable=False)
    )
    op.add_column(
        "artefact_matching_rule", sa.Column("owner", sa.String(length=200), server_default="", nullable=False)
    )

    # drop old unique constraint
    op.drop_constraint(op.f(PREVIOUS_CONSTRAINT_NAME), "artefact_matching_rule", type_="unique")
    # create new one with all fields
    op.create_unique_constraint(
        op.f(NEW_CONSTRAINT_NAME),
        "artefact_matching_rule",
        ["name", "family", "stage", "track", "branch", "store", "series", "os", "release", "owner", "grant_permissions"],
    )


def downgrade() -> None:
    # for the downgrade, to ensure that we don't have duplicate AMRs,
    # we first merge the ones that will become duplicates
    # e.g. same family and different release, both AMRs will be the same
    conn = op.get_bind()

    # partition by the old 5 constraint columns to find duplicates
    find_duplicates_query = sa.text("""
        WITH RankedRules AS (
            SELECT 
                id,
                ROW_NUMBER() OVER(
                    PARTITION BY name, family, stage, track, branch 
                    ORDER BY id ASC
                ) as rn,
                FIRST_VALUE(id) OVER(
                    PARTITION BY name, family, stage, track, branch 
                    ORDER BY id ASC
                ) as survivor_id
            FROM artefact_matching_rule
        )
        SELECT id AS doomed_id, survivor_id 
        FROM RankedRules 
        WHERE rn > 1;
    """)

    duplicates = conn.execute(find_duplicates_query).fetchall()

    if duplicates:
        for doomed_id, survivor_id in duplicates:
            
            # Merge team associations (ON CONFLICT DO NOTHING handles overlap)
            conn.execute(sa.text(f"""
                INSERT INTO {ASSOCIATION_TABLE_NAME} (artefact_matching_rule_id, team_id)
                SELECT :survivor_id, team_id 
                FROM {ASSOCIATION_TABLE_NAME} 
                WHERE artefact_matching_rule_id = :doomed_id
                ON CONFLICT DO NOTHING;
            """), {"survivor_id": survivor_id, "doomed_id": doomed_id})
            
            # Remove old references in the association table
            conn.execute(sa.text(f"""
                DELETE FROM {ASSOCIATION_TABLE_NAME} 
                WHERE artefact_matching_rule_id = :doomed_id;
            """), {"doomed_id": doomed_id})
            
            # Delete the duplicate rule
            conn.execute(sa.text("""
                DELETE FROM artefact_matching_rule 
                WHERE id = :doomed_id;
            """), {"doomed_id": doomed_id})

    # now we can proceed with the downgrade
    # drop new unique constraint
    op.drop_constraint(op.f(NEW_CONSTRAINT_NAME), "artefact_matching_rule", type_="unique")
    
    # drop added columns
    op.drop_column("artefact_matching_rule", "owner")
    op.drop_column("artefact_matching_rule", "release")
    op.drop_column("artefact_matching_rule", "os")
    op.drop_column("artefact_matching_rule", "series")
    op.drop_column("artefact_matching_rule", "store")

    # recreate old, more restrictive unique constraint
    op.create_unique_constraint(
        op.f(PREVIOUS_CONSTRAINT_NAME), "artefact_matching_rule", ["name", "family", "stage", "track", "branch"]
    )
