"""Add version field for Artefacts

Revision ID: e3a483fad7b0
Revises: 465b38949733
Create Date: 2023-05-11 12:34:39.380292+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e3a483fad7b0'
down_revision = '465b38949733'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('artefact', sa.Column('version', sa.String(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_column('artefact', 'version')
    # ### end Alembic commands ###
