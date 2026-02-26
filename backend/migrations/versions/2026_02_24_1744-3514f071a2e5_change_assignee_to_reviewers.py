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

"""Change assignee to reviewers

Revision ID: 3514f071a2e5
Revises: f5f3abf809b3
Create Date: 2026-02-24 17:44:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "3514f071a2e5"
down_revision = "f5f3abf809b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the association table for many-to-many relationship
    op.create_table(
        "artefact_reviewers_association",
        sa.Column("artefact_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["artefact_id"],
            ["artefact.id"],
            name="artefact_reviewers_association_artefact_id_fkey",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["app_user.id"],
            name="artefact_reviewers_association_user_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "artefact_id", "user_id", name="artefact_reviewers_association_pkey"
        ),
    )

    # Migrate existing assignee data to the new association table
    op.execute("""
        INSERT INTO artefact_reviewers_association (artefact_id, user_id)
        SELECT id, assignee_id
        FROM artefact
        WHERE assignee_id IS NOT NULL
    """)

    # Drop the old foreign key constraint and column
    op.drop_constraint("artefact_assignee_id_fkey", "artefact", type_="foreignkey")
    op.drop_index("artefact_assignee_id_ix", table_name="artefact")
    op.drop_column("artefact", "assignee_id")


def downgrade() -> None:
    # Re-add the assignee_id column
    op.add_column(
        "artefact",
        sa.Column("assignee_id", sa.Integer(), nullable=True),
    )
    op.create_index("artefact_assignee_id_ix", "artefact", ["assignee_id"])
    op.create_foreign_key(
        "artefact_assignee_id_fkey",
        "artefact",
        "app_user",
        ["assignee_id"],
        ["id"],
    )

    # Migrate data back (take the first reviewer as the assignee)
    op.execute("""
        UPDATE artefact
        SET assignee_id = (
            SELECT user_id
            FROM artefact_reviewers_association
            WHERE artefact_reviewers_association.artefact_id = artefact.id
            LIMIT 1
        )
    """)

    # Drop the association table
    op.drop_table("artefact_reviewers_association")
