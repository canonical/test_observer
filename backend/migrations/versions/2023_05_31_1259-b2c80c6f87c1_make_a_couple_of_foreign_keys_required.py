"""Make a couple of foreign keys required

Revision ID: b2c80c6f87c1
Revises: bab2d2897e38
Create Date: 2023-05-31 12:59:40.263937+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b2c80c6f87c1"
down_revision = "bab2d2897e38"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("artefact", "stage_id", existing_type=sa.INTEGER(), nullable=False)
    op.alter_column("stage", "family_id", existing_type=sa.INTEGER(), nullable=False)


def downgrade() -> None:
    op.alter_column("stage", "family_id", existing_type=sa.INTEGER(), nullable=True)
    op.alter_column("artefact", "stage_id", existing_type=sa.INTEGER(), nullable=True)
