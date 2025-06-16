"""Add performance indexes for test summary report

Revision ID: fb0d694fb25a
Revises: add_issue_sync_fields
Create Date: 2025-06-16 14:01:19.637921+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fb0d694fb25a'
down_revision = 'add_issue_sync_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Composite index for test summary query optimization
    # This index dramatically speeds up the main query in the test summary endpoint
    op.create_index(
        'artefact_created_at_family_idx', 
        'artefact', 
        ['created_at', 'family'],
        postgresql_include=['id']
    )
    
    # Index for TestCase.name filtering (excludes mir tests)
    op.create_index(
        'test_case_name_template_id_idx',
        'test_case',
        ['name', 'template_id']
    )
    
    # Composite index for the join chain optimization
    op.create_index(
        'test_result_status_case_execution_idx',
        'test_result',
        ['status', 'test_case_id', 'test_execution_id']
    )
    
    # Index for ArtefactBuild -> Artefact join optimization  
    op.create_index(
        'artefact_build_artefact_id_created_at_idx',
        'artefact_build', 
        ['artefact_id'],
        postgresql_include=['id']
    )


def downgrade() -> None:
    op.drop_index('artefact_build_artefact_id_created_at_idx', table_name='artefact_build')
    op.drop_index('test_result_status_case_execution_idx', table_name='test_result')
    op.drop_index('test_case_name_template_id_idx', table_name='test_case')
    op.drop_index('artefact_created_at_family_idx', table_name='artefact')
