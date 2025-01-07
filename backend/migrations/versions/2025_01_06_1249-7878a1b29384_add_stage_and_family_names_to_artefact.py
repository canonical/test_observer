"""Add stage and family names to artefact

Revision ID: 7878a1b29384
Revises: 0e09759a33c3
Create Date: 2025-01-06 12:49:42.039170+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7878a1b29384"
down_revision = "0e09759a33c3"
branch_labels = None
depends_on = None


fill_stages_stmt = """
UPDATE artefact
SET stage = subq.name
FROM (SELECT id, name FROM stage) as subq
WHERE subq.id = artefact.stage_id
"""

fill_family_names_stmt = """
UPDATE artefact
SET family_name = subq.family_name
FROM (
    SELECT stage.id stage_id, family.name family_name
    FROM stage 
    JOIN family ON family.id = stage.family_id
) subq
WHERE subq.stage_id = artefact.stage_id
"""


def upgrade() -> None:
    op.add_column("artefact", sa.Column("stage", sa.String(length=200)))
    op.add_column("artefact", sa.Column("family_name", sa.String(length=200)))

    op.execute(fill_stages_stmt)
    op.execute(fill_family_names_stmt)

    op.alter_column("artefact", "stage", nullable=False)
    op.alter_column("artefact", "family_name", nullable=False)


def downgrade() -> None:
    op.drop_column("artefact", "family_name")
    op.drop_column("artefact", "stage")
