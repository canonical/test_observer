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

"""Migrate reviewer_families to artefact_matching_rules

Revision ID: e9ada0b8b7a4
Revises: a3c0e9e00850
Create Date: 2026-02-09 17:34:00.000000+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'e9ada0b8b7a4'
down_revision = '24f85f32bbb8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create a connection to execute raw SQL
    connection = op.get_bind()
    
    # Get all teams with reviewer_families
    teams = connection.execute(
        sa.text(
            "SELECT id, name, reviewer_families FROM team WHERE array_length(reviewer_families, 1) > 0"
        )
    ).fetchall()
    
    # For each team, create ArtefactMatchingRule entries for each family
    for team_id, team_name, reviewer_families in teams:
        for family in reviewer_families:
            # Check if a matching rule already exists for this family (with all other fields NULL)
            existing_rule = connection.execute(
                sa.text(
                    """
                    SELECT id FROM artefact_matching_rule 
                    WHERE family = :family 
                    AND stage IS NULL 
                    AND track IS NULL 
                    AND branch IS NULL
                    """
                ),
                {"family": family}
            ).fetchone()
            
            if existing_rule:
                rule_id = existing_rule[0]
            else:
                # Create new ArtefactMatchingRule
                result = connection.execute(
                    sa.text(
                        """
                        INSERT INTO artefact_matching_rule (family, stage, track, branch, created_at, updated_at)
                        VALUES (:family, NULL, NULL, NULL, NOW(), NOW())
                        RETURNING id
                        """
                    ),
                    {"family": family}
                )
                first_row = result.fetchone()
                if first_row:
                    rule_id = first_row[0]
                else:
                    raise Exception(f"Failed to create artefact matching rule for family '{family}'")
            
            # Check if association already exists
            existing_association = connection.execute(
                sa.text(
                    """
                    SELECT 1 FROM artefact_matching_rule_team_association
                    WHERE artefact_matching_rule_id = :rule_id AND team_id = :team_id
                    """
                ),
                {"rule_id": rule_id, "team_id": team_id}
            ).fetchone()
            
            if not existing_association:
                # Create association between the rule and the team
                connection.execute(
                    sa.text(
                        """
                        INSERT INTO artefact_matching_rule_team_association (artefact_matching_rule_id, team_id)
                        VALUES (:rule_id, :team_id)
                        """
                    ),
                    {"rule_id": rule_id, "team_id": team_id}
                )
    
    # Drop the reviewer_families column
    op.drop_column('team', 'reviewer_families')


def downgrade() -> None:
    # Re-add the reviewer_families column
    op.add_column(
        'team',
        sa.Column(
            'reviewer_families',
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default='{}'
        )
    )
    
    # Populate reviewer_families from artefact_matching_rules
    connection = op.get_bind()
    
    # Get all teams with their associated matching rules
    teams = connection.execute(
        sa.text(
            """
            SELECT DISTINCT t.id, t.name
            FROM team t
            """
        )
    ).fetchall()
    
    for team_id, team_name in teams:
        # Get all family-only matching rules for this team
        families = connection.execute(
            sa.text(
                """
                SELECT DISTINCT amr.family
                FROM artefact_matching_rule amr
                JOIN artefact_matching_rule_team_association amrta ON amr.id = amrta.artefact_matching_rule_id
                WHERE amrta.team_id = :team_id
                AND amr.stage IS NULL
                AND amr.track IS NULL
                AND amr.branch IS NULL
                """
            ),
            {"team_id": team_id}
        ).fetchall()
        
        if families:
            family_list = [f[0] for f in families]
            connection.execute(
                sa.text(
                    """
                    UPDATE team
                    SET reviewer_families = :families
                    WHERE id = :team_id
                    """
                ),
                {"families": family_list, "team_id": team_id}
            )
