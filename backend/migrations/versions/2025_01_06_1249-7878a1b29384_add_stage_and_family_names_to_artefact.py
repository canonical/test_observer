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

fill_families_stmt = """
UPDATE artefact
SET family = subq.family
FROM (
    SELECT stage.id stage_id, family.name family
    FROM stage 
    JOIN family ON family.id = stage.family_id
) subq
WHERE subq.stage_id = artefact.stage_id
"""


def upgrade() -> None:
    op.add_column("artefact", sa.Column("stage", sa.String(length=200)))
    op.add_column("artefact", sa.Column("family", sa.String(length=200)))

    op.execute(fill_stages_stmt)
    op.execute(fill_families_stmt)

    op.alter_column("artefact", "stage", nullable=False)
    op.alter_column("artefact", "family", nullable=False)

    op.drop_index("artefact_stage_id_ix", table_name="artefact")
    op.drop_constraint("artefact_stage_id_fkey", "artefact", type_="foreignkey")
    op.drop_column("artefact", "stage_id")


fill_stage_id_stmt = """
UPDATE artefact
SET stage_id = subq.stage_id
FROM (
    SELECT stage.id stage_id, stage.name stage_name, family.name family_name
    FROM stage
    JOIN family ON family.id = stage.family_id
) subq
WHERE subq.stage_name = artefact.stage AND subq.family_name = artefact.family
"""


def downgrade() -> None:
    op.add_column(
        "artefact",
        sa.Column("stage_id", sa.INTEGER(), autoincrement=False),
    )

    op.execute(fill_stage_id_stmt)
    op.alter_column("artefact", "stage_id", nullable=False)
    op.create_foreign_key(
        "artefact_stage_id_fkey",
        "artefact",
        "stage",
        ["stage_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("artefact_stage_id_ix", "artefact", ["stage_id"], unique=False)

    op.drop_column("artefact", "family")
    op.drop_column("artefact", "stage")
