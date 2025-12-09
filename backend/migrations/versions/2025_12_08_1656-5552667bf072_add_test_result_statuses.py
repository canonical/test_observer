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

"""add test_result_statuses

Revision ID: 5552667bf072
Revises: c3f90b376843
Create Date: 2025-12-08 16:56:37.037889+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5552667bf072'
down_revision = 'c3f90b376843'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add test_result_statuses column to issue_test_result_attachment_rule table
    op.add_column('issue_test_result_attachment_rule', sa.Column('test_result_statuses', postgresql.ARRAY(sa.Enum('PASSED', 'FAILED', 'SKIPPED', name='testresultstatus')), nullable=False))


def downgrade() -> None:
    # drop test_result_statuses column from issue_test_result_attachment_rule table
    op.drop_column('issue_test_result_attachment_rule', 'test_result_statuses')
