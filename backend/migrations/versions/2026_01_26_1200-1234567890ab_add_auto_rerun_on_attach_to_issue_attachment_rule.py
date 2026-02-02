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

"""add auto_rerun_on_attach to IssueTestResultAttachmentRule

Revision ID: 1234567890ab
Revises: 5552667bf072
Create Date: 2026-01-26 12:00:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1234567890ab"
down_revision = "5552667bf072"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add auto_rerun_on_attach column to issue_test_result_attachment_rule table
    op.add_column(
        "issue_test_result_attachment_rule",
        sa.Column(
            "auto_rerun_on_attach",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    # drop auto_rerun_on_attach column from issue_test_result_attachment_rule table
    op.drop_column("issue_test_result_attachment_rule", "auto_rerun_on_attach")

