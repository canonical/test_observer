"""Add basic v0 models

Revision ID: 465b38949733
Revises:
Create Date: 2023-05-04 10:00:05.067853+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '465b38949733'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('artefact_group',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('version_pattern', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_artefact_group_name'), 'artefact_group', ['name'], unique=True)
    op.create_table('environment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_environment_name'), 'environment', ['name'], unique=True)
    op.create_table('family',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_name'), 'family', ['name'], unique=True)
    op.create_table('expected_environment',
    sa.Column('artefact_group_id', sa.Integer(), nullable=False),
    sa.Column('environment_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['artefact_group_id'], ['artefact_group.id'], ),
    sa.ForeignKeyConstraint(['environment_id'], ['environment.id'], ),
    sa.PrimaryKeyConstraint('artefact_group_id', 'environment_id')
    )
    op.create_table('stage',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('family_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['family_id'], ['family.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stage_name'), 'stage', ['name'], unique=True)
    op.create_index(op.f('ix_stage_position'), 'stage', ['position'], unique=False)
    op.create_table('artefact',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('source', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('due_date', sa.Date(), nullable=True),
    sa.Column('status', sa.Enum('Approved', 'Marked as Failed', name='artefact_status_enum'), nullable=True),
    sa.Column('stage_id', sa.Integer(), nullable=True),
    sa.Column('artefact_group_id', sa.Integer(), nullable=True),
    sa.Column('is_archived', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.ForeignKeyConstraint(['artefact_group_id'], ['artefact_group.id'], ),
    sa.ForeignKeyConstraint(['stage_id'], ['stage.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_artefact_name'), 'artefact', ['name'], unique=False)
    op.create_table('test_execution',
    sa.Column('artefact_id', sa.Integer(), nullable=False),
    sa.Column('environment_id', sa.Integer(), nullable=False),
    sa.Column('jenkins_link', sa.String(length=200), nullable=True),
    sa.Column('c3_link', sa.String(length=200), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('status', sa.Enum('Not Started', 'In Progress', 'Passed', 'Failed', 'Not Tested', name='test_status_enum'), server_default='Not Started', nullable=False),
    sa.ForeignKeyConstraint(['artefact_id'], ['artefact.id'], ),
    sa.ForeignKeyConstraint(['environment_id'], ['environment.id'], ),
    sa.PrimaryKeyConstraint('artefact_id', 'environment_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_table('test_execution')
    op.drop_index(op.f('ix_artefact_name'), table_name='artefact')
    op.drop_table('artefact')
    op.drop_index(op.f('ix_stage_position'), table_name='stage')
    op.drop_index(op.f('ix_stage_name'), table_name='stage')
    op.drop_table('stage')
    op.drop_table('expected_environment')
    op.drop_index(op.f('ix_family_name'), table_name='family')
    op.drop_table('family')
    op.drop_index(op.f('ix_environment_name'), table_name='environment')
    op.drop_table('environment')
    op.drop_index(op.f('ix_artefact_group_name'), table_name='artefact_group')
    op.drop_table('artefact_group')
    # ### end Alembic commands ###
