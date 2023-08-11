"""Unique constraint with NULL revision for artefact_build

Revision ID: ce0b50f657e9
Revises: 18b1066d92c3
Create Date: 2023-08-11 11:51:06.475246+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ce0b50f657e9'
down_revision = '18b1066d92c3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('artefact_build_artefact_id_architecture_revision_key', 'artefact_build', type_='unique')
    op.drop_index('unique_artefact_build_null_revision', table_name='artefact_build')
    op.create_index('idx_artefact_id_architecture_null_revision', 'artefact_build', ['artefact_id', 'architecture'], unique=True, postgresql_where=sa.text('revision IS NULL'))
    op.create_index('idx_artefact_id_architecture_revision', 'artefact_build', ['artefact_id', 'architecture', 'revision'], unique=True, postgresql_where=sa.text('revision IS NOT NULL'))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('idx_artefact_id_architecture_revision', table_name='artefact_build', postgresql_where=sa.text('revision IS NOT NULL'))
    op.drop_index('idx_artefact_id_architecture_null_revision', table_name='artefact_build', postgresql_where=sa.text('revision IS NULL'))
    op.create_index('unique_artefact_build_null_revision', 'artefact_build', ['artefact_id', 'architecture'], unique=False)
    op.create_unique_constraint('artefact_build_artefact_id_architecture_revision_key', 'artefact_build', ['artefact_id', 'architecture', 'revision'])
    # ### end Alembic commands ###
