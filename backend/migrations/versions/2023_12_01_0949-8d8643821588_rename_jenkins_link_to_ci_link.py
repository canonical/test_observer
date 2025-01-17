# Copyright (C) 2023 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Rename jenkins_link to ci_link

Revision ID: 8d8643821588
Revises: 49221114815a
Create Date: 2023-12-01 09:49:44.849714+00:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "8d8643821588"
down_revision = "49221114815a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("test_execution", "jenkins_link", new_column_name="ci_link")


def downgrade() -> None:
    op.alter_column("test_execution", "ci_link", new_column_name="jenkins_link")
