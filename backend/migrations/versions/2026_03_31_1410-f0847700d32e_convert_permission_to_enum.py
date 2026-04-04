# Copyright 2026 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Change permissions attributes from string to enum

Revision ID: f0847700d32e
Revises: c29b4f545a9b
Create Date: 2026-03-31 14:10:46.747275+00:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f0847700d32e"
down_revision = "c29b4f545a9b"
branch_labels = None
depends_on = None

PERMISSION_TYPE = postgresql.ARRAY(postgresql.ENUM(name="permission"))


def upgrade() -> None:
    # upgrade application table

    # drop default to prevent casting errors from postgresql
    op.execute("ALTER TABLE application ALTER COLUMN permissions DROP DEFAULT")

    # change type
    op.alter_column(
        "application",
        "permissions",
        existing_type=postgresql.ARRAY(sa.VARCHAR()),
        type_=PERMISSION_TYPE,
        existing_nullable=False,
        postgresql_using="permissions::permission[]",
    )

    # apply new default
    op.execute("ALTER TABLE application ALTER COLUMN permissions SET DEFAULT '{}'::permission[]")

    # upgrade team table
    # drop default to prevent casting errors from postgresql
    op.execute("ALTER TABLE team ALTER COLUMN permissions DROP DEFAULT")

    # change type
    op.alter_column(
        "team",
        "permissions",
        existing_type=postgresql.ARRAY(sa.VARCHAR()),
        type_=PERMISSION_TYPE,
        existing_nullable=False,
        postgresql_using="permissions::permission[]",
    )

    # apply new default
    op.execute("ALTER TABLE team ALTER COLUMN permissions SET DEFAULT '{}'::permission[]")


def downgrade() -> None:
    # downgrade team table
    # drop default
    op.execute("ALTER TABLE team ALTER COLUMN permissions DROP DEFAULT")

    # convert
    op.alter_column(
        "team",
        "permissions",
        existing_type=PERMISSION_TYPE,
        type_=postgresql.ARRAY(sa.VARCHAR()),
        existing_nullable=False,
        postgresql_using="permissions::varchar[]",
    )

    # restore previous default
    op.execute("ALTER TABLE team ALTER COLUMN permissions SET DEFAULT '{}'::character varying[]")

    # drop default
    op.execute("ALTER TABLE application ALTER COLUMN permissions DROP DEFAULT")

    # upgrade application table
    op.alter_column(
        "application",
        "permissions",
        existing_type=PERMISSION_TYPE,
        type_=postgresql.ARRAY(sa.VARCHAR()),
        existing_nullable=False,
        postgresql_using="permissions::varchar[]",
    )

    # restore previous default
    op.execute("ALTER TABLE application ALTER COLUMN permissions SET DEFAULT '{}'::character varying[]")
