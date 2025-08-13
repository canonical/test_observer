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

"""Enforce uniqueness on attachment rule metadata

Revision ID: 09aaaefce90d
Revises: 18ddcbd0fe0b
Create Date: 2025-08-12 20:43:18.884545+00:00

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "09aaaefce90d"
down_revision = "18ddcbd0fe0b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        op.f(
            "issue_test_result_attachment_rule_execution_metadata_attachment_rule_id_category_value_key"
        ),
        "issue_test_result_attachment_rule_execution_metadata",
        ["attachment_rule_id", "category", "value"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f(
            "issue_test_result_attachment_rule_execution_metadata_attachment_rule_id_category_value_key"
        ),
        "issue_test_result_attachment_rule_execution_metadata",
        type_="unique",
    )
