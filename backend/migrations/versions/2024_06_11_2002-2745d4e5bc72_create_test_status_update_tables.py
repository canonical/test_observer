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

"""Create test status update tables

Revision ID: 2745d4e5bc72
Revises: 33c0383ea9ca
Create Date: 2024-06-11 20:02:00.064753+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2745d4e5bc72"
down_revision = "33c0383ea9ca"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "test_event",
        sa.Column("event_name", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("detail", sa.String(), nullable=False),
        sa.Column("test_execution_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["test_execution_id"],
            ["test_execution.id"],
            name=op.f("test_event_test_execution_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("test_event_pkey")),
    )
    # ### end Alembic commands ###
    op.execute(
        "ALTER TABLE test_execution ADD COLUMN "
        "resource_url VARCHAR NOT NULL DEFAULT ''"
    )

    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE testexecutionstatus ADD VALUE 'ENDED_PREMATURELY'")


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("test_event")
    # ### end Alembic commands ###
    op.execute("ALTER TYPE testexecutionstatus RENAME TO testexecutionstatus_old")
    op.execute(
        "CREATE TYPE testexecutionstatus AS "
        "ENUM('NOT_STARTED', 'IN_PROGRESS', 'PASSED', 'FAILED', 'NOT_TESTED')"
    )
    op.execute(
        "ALTER TABLE test_execution ALTER COLUMN status TYPE testexecutionstatus USING "
        "status::text::testexecutionstatus"
    )
    op.execute("DROP TYPE testexecutionstatus_old")
    op.drop_column("test_execution", "resource_url")
