# Copyright 2024 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Drop review columns from Test Execution Table

Revision ID: b234def463ad
Revises: 91e7e3f437a0
Create Date: 2024-10-18 11:34:38.285303+00:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b234def463ad"
down_revision = "91e7e3f437a0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("test_execution", "review_decision")
    op.drop_column("test_execution", "review_comment")
    op.execute("DROP TYPE testexecutionreviewdecision")


def downgrade() -> None:
    te_review_decision = sa.Enum(
        "REJECTED",
        "APPROVED_INCONSISTENT_TEST",
        "APPROVED_UNSTABLE_PHYSICAL_INFRA",
        "APPROVED_FAULTY_HARDWARE",
        "APPROVED_CUSTOMER_PREREQUISITE_FAIL",
        "APPROVED_ALL_TESTS_PASS",
        name="testexecutionreviewdecision",
    )
    te_review_decision.create(op.get_bind())
    op.add_column(
        "test_execution",
        sa.Column(
            "review_comment",
            sa.VARCHAR(),
            server_default=sa.text("''::character varying"),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.add_column(
        "test_execution",
        sa.Column(
            "review_decision",
            postgresql.ARRAY(te_review_decision),
            server_default=sa.text("'{}'::testexecutionreviewdecision[]"),
            autoincrement=False,
            nullable=False,
        ),
    )
