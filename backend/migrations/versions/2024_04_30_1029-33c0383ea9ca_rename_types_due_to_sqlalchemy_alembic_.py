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

"""Rename types due to sqlalchemy/alembic upgrade

Revision ID: 33c0383ea9ca
Revises: 08bc88dcb1e1
Create Date: 2024-04-30 10:29:23.440961+00:00

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "33c0383ea9ca"
down_revision = "08bc88dcb1e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE artefact_status_enum RENAME TO artefactstatus")
    op.execute("ALTER TYPE test_status_enum RENAME TO testexecutionstatus")


def downgrade() -> None:
    op.execute("ALTER TYPE artefactstatus RENAME TO artefact_status_enum")
    op.execute("ALTER TYPE testexecutionstatus RENAME TO test_status_enum")
