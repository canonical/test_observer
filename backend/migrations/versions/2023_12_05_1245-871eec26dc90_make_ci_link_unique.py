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

"""Make ci_link unique

Revision ID: 871eec26dc90
Revises: f59da052cbac
Create Date: 2023-12-05 12:45:25.467951+00:00

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "871eec26dc90"
down_revision = "f59da052cbac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        op.f("test_execution_ci_link_key"), "test_execution", ["ci_link"]
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("test_execution_ci_link_key"), "test_execution", type_="unique"
    )
