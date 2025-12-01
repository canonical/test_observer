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

"""restructure_rerun_request_with_three_fks

Revision ID: c3f90b376843
Revises: b329c0aa09ac
Create Date: 2025-11-26 20:20:47.869601+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3f90b376843'
down_revision = 'b329c0aa09ac'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns (nullable initially)
    op.add_column('test_execution_rerun_request', sa.Column('test_plan_id', sa.Integer(), nullable=True))
    op.add_column('test_execution_rerun_request', sa.Column('artefact_build_id', sa.Integer(), nullable=True))
    op.add_column('test_execution_rerun_request', sa.Column('environment_id', sa.Integer(), nullable=True))
    
    # Populate new columns from test_execution
    op.execute("""
        UPDATE test_execution_rerun_request terr
        SET test_plan_id = te.test_plan_id,
            artefact_build_id = te.artefact_build_id,
            environment_id = te.environment_id
        FROM test_execution te
        WHERE terr.test_execution_id = te.id
    """)
    
    # Delete orphaned rerun requests (where test_execution was deleted)
    op.execute("""
        DELETE FROM test_execution_rerun_request
        WHERE test_plan_id IS NULL OR artefact_build_id IS NULL OR environment_id IS NULL
    """)
    
    # Deduplicate rerun requests
    op.execute("""
        DELETE FROM test_execution_rerun_request
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM test_execution_rerun_request
            GROUP BY test_plan_id, artefact_build_id, environment_id
        )
    """)
    
    # Make columns NOT NULL
    op.alter_column('test_execution_rerun_request', 'test_plan_id', nullable=False)
    op.alter_column('test_execution_rerun_request', 'artefact_build_id', nullable=False)
    op.alter_column('test_execution_rerun_request', 'environment_id', nullable=False)
    
    # Drop old foreign key and unique constraint on test_execution_id
    op.drop_constraint('test_execution_rerun_request_test_execution_id_fkey', 
                      'test_execution_rerun_request', type_='foreignkey')
    op.drop_constraint('test_execution_rerun_request_test_execution_id_key',
                      'test_execution_rerun_request', type_='unique')
    
    # Add new foreign keys
    op.create_foreign_key(
        'fk_rerun_request_test_plan',
        'test_execution_rerun_request', 'test_plan',
        ['test_plan_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_rerun_request_artefact_build',
        'test_execution_rerun_request', 'artefact_build',
        ['artefact_build_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_rerun_request_environment',
        'test_execution_rerun_request', 'environment',
        ['environment_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Add unique constraint on the group
    op.create_unique_constraint('uq_rerun_request_group', 
                               'test_execution_rerun_request', 
                               ['test_plan_id', 'artefact_build_id', 'environment_id'])
    
    # Add indexes
    op.create_index('idx_rerun_request_test_plan_id', 'test_execution_rerun_request', ['test_plan_id'])
    op.create_index('idx_rerun_request_artefact_build_id', 'test_execution_rerun_request', ['artefact_build_id'])
    op.create_index('idx_rerun_request_environment_id', 'test_execution_rerun_request', ['environment_id'])
    
    # Drop old test_execution_id column
    op.drop_column('test_execution_rerun_request', 'test_execution_id')


def downgrade() -> None:
    # Re-add test_execution_id column
    op.add_column('test_execution_rerun_request', 
                 sa.Column('test_execution_id', sa.Integer(), nullable=True))
    
    # Populate from latest test_execution for each group
    op.execute("""
        UPDATE test_execution_rerun_request terr
        SET test_execution_id = (
            SELECT te.id 
            FROM test_execution te 
            WHERE te.test_plan_id = terr.test_plan_id
              AND te.artefact_build_id = terr.artefact_build_id
              AND te.environment_id = terr.environment_id
            ORDER BY te.id DESC
            LIMIT 1
        )
    """)
    
    # Make test_execution_id NOT NULL
    op.alter_column('test_execution_rerun_request', 'test_execution_id', nullable=False)
    
    # Drop indexes
    op.drop_index('idx_rerun_request_environment_id', table_name='test_execution_rerun_request')
    op.drop_index('idx_rerun_request_artefact_build_id', table_name='test_execution_rerun_request')
    op.drop_index('idx_rerun_request_test_plan_id', table_name='test_execution_rerun_request')
    
    # Drop unique constraint and foreign keys
    op.drop_constraint('uq_rerun_request_group', 'test_execution_rerun_request', type_='unique')
    op.drop_constraint('fk_rerun_request_environment', 'test_execution_rerun_request', type_='foreignkey')
    op.drop_constraint('fk_rerun_request_artefact_build', 'test_execution_rerun_request', type_='foreignkey')
    op.drop_constraint('fk_rerun_request_test_plan', 'test_execution_rerun_request', type_='foreignkey')
    
    # Re-add old foreign key on test_execution_id
    op.create_foreign_key(
        'test_execution_rerun_request_test_execution_id_fkey',
        'test_execution_rerun_request', 'test_execution',
        ['test_execution_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_unique_constraint('test_execution_rerun_request_test_execution_id_key',
                               'test_execution_rerun_request', ['test_execution_id'])
    
    # Drop new columns
    op.drop_column('test_execution_rerun_request', 'environment_id')
    op.drop_column('test_execution_rerun_request', 'artefact_build_id')
    op.drop_column('test_execution_rerun_request', 'test_plan_id')
