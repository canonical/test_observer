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

"""Add reviewer_families to teams

Revision ID: 2ddd55f913eb
Revises: 3f6a99085db7
Create Date: 2025-11-07 08:56:00.000000+00:00

"""

from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy import insert, select, update
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import column, table

# revision identifiers, used by Alembic.
revision = "2ddd55f913eb"
down_revision = "3f6a99085db7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add reviewer_families array column to team table
    op.add_column(
        "team",
        sa.Column(
            "reviewer_families",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
    )

    # Migrate existing is_reviewer users to certification-reviewers team
    connection = op.get_bind()

    # Define tables for migration
    team_table = table(
        "team",
        column("id", sa.Integer),
        column("name", sa.String),
        column("permissions", postgresql.ARRAY(sa.String())),
        column("reviewer_families", postgresql.ARRAY(sa.String())),
        column("created_at", sa.DateTime),
        column("updated_at", sa.DateTime),
    )

    user_table = table(
        "app_user",
        column("id", sa.Integer),
        column("is_reviewer", sa.Boolean),
    )

    team_users_table = table(
        "team_users_association",
        column("user_id", sa.Integer),
        column("team_id", sa.Integer),
    )

    def create_team_if_doesnt_exist(team_name: str, reviewer_families: list[str]) -> int:
        select_result = connection.execute(select(team_table.c.id).where(team_table.c.name == team_name)).first()
        if select_result is None:
            now = datetime.now(UTC)
            insert_result = connection.execute(
                insert(team_table)
                .values(
                    name=team_name,
                    permissions=[],
                    reviewer_families=reviewer_families,
                    created_at=now,
                    updated_at=now,
                )
                .returning(team_table.c.id)
            )
            if (row := insert_result.fetchone()) is None:
                raise Exception("Failed to create team")
            return row[0]
        return select_result[0]

    # Get all users with is_reviewer=True
    reviewers = connection.execute(select(user_table.c.id).where(user_table.c.is_reviewer.is_(True))).fetchall()

    # Only create certification-reviewers team if there are reviewers to migrate
    if reviewers:
        cert_team_id = create_team_if_doesnt_exist("certification-reviewers", ["snap", "deb", "image"])

        # Add them to the certification-reviewers team
        # Check which users are not already in the team
        for reviewer in reviewers:
            user_id = reviewer[0]
            exists = connection.execute(
                select(team_users_table.c.user_id)
                .where(team_users_table.c.user_id == user_id)
                .where(team_users_table.c.team_id == cert_team_id)
            ).first()

            if not exists:
                connection.execute(
                    insert(team_users_table).values(
                        user_id=user_id,
                        team_id=cert_team_id,
                    )
                )

    # Drop the is_reviewer column
    op.drop_column("app_user", "is_reviewer")


def downgrade() -> None:
    # Add back is_reviewer column
    op.add_column(
        "app_user",
        sa.Column("is_reviewer", sa.Boolean(), nullable=False, server_default="false"),
    )

    # Restore is_reviewer for users in certification-reviewers team
    connection = op.get_bind()

    team_table = table(
        "team",
        column("id", sa.Integer),
        column("name", sa.String),
    )

    user_table = table(
        "app_user",
        column("id", sa.Integer),
        column("is_reviewer", sa.Boolean),
    )

    team_users_table = table(
        "team_users_association",
        column("user_id", sa.Integer),
        column("team_id", sa.Integer),
    )

    # Get certification-reviewers team id
    result = connection.execute(select(team_table.c.id).where(team_table.c.name == "certification-reviewers")).first()

    if result:
        cert_team_id = result[0]
        # Get all users in the certification-reviewers team
        members = connection.execute(
            select(team_users_table.c.user_id).where(team_users_table.c.team_id == cert_team_id)
        ).fetchall()

        # Set is_reviewer=True for those users
        for member in members:
            connection.execute(update(user_table).where(user_table.c.id == member[0]).values(is_reviewer=True))

    # Drop reviewer_families from team
    op.drop_column("team", "reviewer_families")
