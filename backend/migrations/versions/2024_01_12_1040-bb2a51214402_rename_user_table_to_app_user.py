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

"""Rename user table to app_user

Revision ID: bb2a51214402
Revises: c9851b127edc
Create Date: 2024-01-12 10:40:00.596887+00:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "bb2a51214402"
down_revision = "c9851b127edc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('ALTER TABLE "user" RENAME TO app_user')
    op.drop_constraint("user_launchpad_email_key", "app_user", type_="unique")
    op.create_unique_constraint(
        op.f("app_user_launchpad_email_key"), "app_user", ["launchpad_email"]
    )


def downgrade() -> None:
    op.execute('ALTER TABLE app_user RENAME TO "user"')
    op.drop_constraint(op.f("app_user_launchpad_email_key"), "user", type_="unique")
    op.create_unique_constraint("user_launchpad_email_key", "user", ["launchpad_email"])
