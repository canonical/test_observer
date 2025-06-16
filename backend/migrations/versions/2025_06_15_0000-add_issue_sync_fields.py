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


"""Add issue sync status tracking fields

Revision ID: add_issue_sync_fields
Revises: 87f9e68e61a7
Create Date: 2025-06-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_issue_sync_fields'
down_revision = '87f9e68e61a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new enums
    issue_status_enum = sa.Enum('OPEN', 'CLOSED', 'UNKNOWN', name='issuestatus')
    issue_sync_status_enum = sa.Enum(
        'NEVER_SYNCED', 'SYNCED', 'SYNC_FAILED', name='issuesyncstatus'
    )
    
    issue_status_enum.create(op.get_bind())
    issue_sync_status_enum.create(op.get_bind())
    
    # Add new columns to test_case_issue table
    op.add_column(
        'test_case_issue', sa.Column('external_id', sa.String(), nullable=True)
    )
    op.add_column(
        'test_case_issue',
        sa.Column(
            'issue_status',
            issue_status_enum,
            nullable=False,
            server_default='UNKNOWN'
        )
    )
    op.add_column(
        'test_case_issue',
        sa.Column(
            'sync_status',
            issue_sync_status_enum,
            nullable=False,
            server_default='NEVER_SYNCED'
        )
    )
    op.add_column(
        'test_case_issue',
        sa.Column('last_synced_at', sa.DateTime(), nullable=True)
    )
    op.add_column(
        'test_case_issue', sa.Column('sync_error', sa.String(), nullable=True)
    )
    
    # Add new columns to environment_issue table
    op.add_column(
        'environment_issue', sa.Column('external_id', sa.String(), nullable=True)
    )
    op.add_column(
        'environment_issue',
        sa.Column(
            'issue_status',
            issue_status_enum,
            nullable=False,
            server_default='UNKNOWN'
        )
    )
    op.add_column(
        'environment_issue',
        sa.Column(
            'sync_status',
            issue_sync_status_enum,
            nullable=False,
            server_default='NEVER_SYNCED'
        )
    )
    op.add_column(
        'environment_issue',
        sa.Column('last_synced_at', sa.DateTime(), nullable=True)
    )
    op.add_column(
        'environment_issue', sa.Column('sync_error', sa.String(), nullable=True)
    )
    
    # Create indexes on external_id fields for performance
    op.create_index(
        'test_case_issue_external_id_ix', 'test_case_issue', ['external_id']
    )
    op.create_index(
        'environment_issue_external_id_ix', 'environment_issue', ['external_id']
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('environment_issue_external_id_ix', table_name='environment_issue')
    op.drop_index('test_case_issue_external_id_ix', table_name='test_case_issue')
    
    # Drop columns from environment_issue table
    op.drop_column('environment_issue', 'sync_error')
    op.drop_column('environment_issue', 'last_synced_at')
    op.drop_column('environment_issue', 'sync_status')
    op.drop_column('environment_issue', 'issue_status')
    op.drop_column('environment_issue', 'external_id')
    
    # Drop columns from test_case_issue table
    op.drop_column('test_case_issue', 'sync_error')
    op.drop_column('test_case_issue', 'last_synced_at')
    op.drop_column('test_case_issue', 'sync_status')
    op.drop_column('test_case_issue', 'issue_status')
    op.drop_column('test_case_issue', 'external_id')
    
    # Drop enums
    sa.Enum(name='issuesyncstatus').drop(op.get_bind())
    sa.Enum(name='issuestatus').drop(op.get_bind())