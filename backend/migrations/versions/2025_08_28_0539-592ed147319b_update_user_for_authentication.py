# Copyright 2025 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Update user for authentication

Revision ID: 592ed147319b
Revises: 09aaaefce90d
Create Date: 2025-08-28 05:39:18.259371+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "592ed147319b"
down_revision = "09aaaefce90d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("app_user", "launchpad_email", new_column_name="email")
    op.execute("ALTER TABLE app_user RENAME CONSTRAINT app_user_launchpad_email_key TO app_user_email_key")
    op.alter_column("app_user", "launchpad_handle", nullable=True)
    op.add_column(
        "app_user",
        sa.Column(
            "is_reviewer",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
    )


def downgrade() -> None:
    op.drop_column("app_user", "is_reviewer")
    # Downgrading is an issue if we have a user with no launchpad_handle
    op.alter_column("app_user", "launchpad_handle", nullable=False)
    op.execute("ALTER TABLE app_user RENAME CONSTRAINT app_user_email_key TO app_user_launchpad_email_key")
    op.alter_column("app_user", "email", new_column_name="launchpad_email")
