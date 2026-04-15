
"""Add all Artefact attributes to ArtefactMatchingRules

Revision ID: d9c144615947
Revises: f0847700d32e
Create Date: 2026-04-15 22:58:28.960881+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd9c144615947'
down_revision = 'f0847700d32e'
branch_labels = None
depends_on = None


PREVIOUS_CONSTRAINT_NAME='artefact_matching_rule_name_family_stage_track_branch_key'
NEW_CONSTRAINT_NAME='artefact_matching_rule_name_family_stage_track_branch_store_series_os_release_owner_key'


def upgrade() -> None:
    op.add_column('artefact_matching_rule', sa.Column('store', sa.String(), server_default='', nullable=False))
    op.add_column('artefact_matching_rule', sa.Column('series', sa.String(), nullable=False))
    op.add_column('artefact_matching_rule', sa.Column('os', sa.String(length=200), nullable=False))
    op.add_column('artefact_matching_rule', sa.Column('release', sa.String(length=200), nullable=False))
    op.add_column('artefact_matching_rule', sa.Column('owner', sa.String(length=200), nullable=False))

    # drop old unique constraint
    op.drop_constraint(op.f(PREVIOUS_CONSTRAINT_NAME), 'artefact_matching_rule', type_='unique')
    # create new one with all fields
    op.create_unique_constraint(op.f(NEW_CONSTRAINT_NAME), 'artefact_matching_rule', ['name', 'family', 'stage', 'track', 'branch', 'store', 'series', 'os', 'release', 'owner'])


def downgrade() -> None:
    # drop new unique constraint
    op.drop_constraint(op.f(NEW_CONSTRAINT_NAME), 'artefact_matching_rule', type_='unique')
    # recreate old one
    op.create_unique_constraint(op.f(PREVIOUS_CONSTRAINT_NAME), 'artefact_matching_rule', ['name', 'family', 'stage', 'track', 'branch'])
    op.drop_column('artefact_matching_rule', 'owner')
    op.drop_column('artefact_matching_rule', 'release')
    op.drop_column('artefact_matching_rule', 'os')
    op.drop_column('artefact_matching_rule', 'series')
    op.drop_column('artefact_matching_rule', 'store')
