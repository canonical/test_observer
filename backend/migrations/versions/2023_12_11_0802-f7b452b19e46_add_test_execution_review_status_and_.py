# Copyright 2023 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Add test execution review decision and comment

Revision ID: f7b452b19e46
Revises: b8e8c3053273
Create Date: 2023-12-11 08:02:27.583110+00:00

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "f7b452b19e46"
down_revision = "b8e8c3053273"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE testexecutionreviewdecision AS "
        "ENUM( "
        "'REJECTED', "
        "'APPROVED_INCONSISTENT_TEST', "
        "'APPROVED_UNSTABLE_PHYSICAL_INFRA', "
        "'APPROVED_FAULTY_HARDWARE', "
        "'APPROVED_CUSTOMER_PREREQUISITE_FAIL', "
        "'APPROVED_ALL_TESTS_PASS' "
        ")"
    )
    op.execute(
        "ALTER TABLE test_execution ADD COLUMN "
        "review_decision testexecutionreviewdecision[] NOT NULL "
        "DEFAULT '{}'::testexecutionreviewdecision[]"
    )
    op.execute(
        "ALTER TABLE test_execution ADD COLUMN "
        "review_comment VARCHAR NOT NULL DEFAULT ''"
    )


def downgrade() -> None:
    op.drop_column("test_execution", "review_comment")
    op.drop_column("test_execution", "review_decision")
    op.execute("DROP TYPE testexecutionreviewdecision")
