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

"""Tests for migration daf0503863d7: add_sentry_debug_permission"""

from collections.abc import Generator
from urllib.parse import urlparse, urlunparse

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy_utils import create_database, database_exists, drop_database  # type: ignore[import-untyped]

# Migration revision constants
PREVIOUS_REV = "d9c144615947"
TARGET_REV = "daf0503863d7"


@pytest.fixture
def migration_context(db_url: str) -> Generator[tuple[Engine, Config], None, None]:
    """
    Create an isolated database context for migration testing.

    Yields:
        tuple: (SQLAlchemy Engine, Alembic Config) for the test database
    """
    # Parse the URL and create a unique test database name
    parsed = urlparse(db_url)
    test_db_url = urlunparse(
        (parsed.scheme, parsed.netloc, "/test_migration_sentry_debug", parsed.params, parsed.query, parsed.fragment)
    )

    # Clean up any existing test database
    if database_exists(test_db_url):
        drop_database(test_db_url)

    # Create new test database
    create_database(test_db_url)

    engine = None
    try:
        # Initialize engine and alembic config
        engine = create_engine(test_db_url)
        alembic_config = Config("alembic.ini")
        alembic_config.set_main_option("sqlalchemy.url", test_db_url)

        yield engine, alembic_config

    finally:
        # Cleanup: dispose engine and drop database
        if engine:
            engine.dispose()
        if database_exists(test_db_url):
            drop_database(test_db_url)


def test_upgrade_and_downgrade_new_permission(migration_context: tuple[Engine, Config]) -> None:
    """
    Test that the new permission can be used after upgrade,
    and is correctly stripped out during a downgrade without losing other permissions.
    """
    engine, alembic_config = migration_context

    # Step 1: Migrate to revision before the target migration
    command.upgrade(alembic_config, PREVIOUS_REV)

    # Insert test data with old permissions
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO team (name, permissions, created_at, updated_at) 
            VALUES 
                ('team_old_only', '{"view_user"}'::permission[], NOW(), NOW()),
                ('team_empty_perms', '{}'::permission[], NOW(), NOW())
        """)
        )

    # Step 2: Upgrade to the target migration
    command.upgrade(alembic_config, TARGET_REV)

    # Step 3: Verify the new enum type includes the new permission by inserting and updating rows
    with engine.begin() as conn:
        # Insert a team with only the new permission
        conn.execute(
            text("""
            INSERT INTO team (name, permissions, created_at, updated_at) 
            VALUES ('team_new_only', '{"view_sentry_debug"}'::permission[], NOW(), NOW())
        """)
        )
        # Update a team to have both an old permission and the new permission
        conn.execute(
            text("""
            UPDATE team 
            SET permissions = array_append(permissions, 'view_sentry_debug'::permission) 
            WHERE name = 'team_old_only'
        """)
        )

    # Verify data after upgrade
    with engine.connect() as conn:
        results = conn.execute(text("SELECT name, permissions::text[] FROM team ORDER BY name")).fetchall()
        permissions_by_team = {row[0]: row[1] for row in results}

        assert "view_sentry_debug" in permissions_by_team["team_new_only"]
        assert set(permissions_by_team["team_old_only"]) == {"view_user", "view_sentry_debug"}

    # Step 4: Downgrade back to the previous version
    command.downgrade(alembic_config, PREVIOUS_REV)

    # Step 5: Verify the new permission was safely stripped away, while preserving old permissions
    with engine.connect() as conn:
        results = conn.execute(text("SELECT name, permissions::text[] FROM team ORDER BY name")).fetchall()
        permissions_by_team = {row[0]: row[1] for row in results}

        # team_new_only had ONLY view_sentry_debug, so it should now have an empty array
        assert len(permissions_by_team["team_new_only"]) == 0

        # team_old_only should have lost view_sentry_debug but kept view_user
        assert set(permissions_by_team["team_old_only"]) == {"view_user"}


def test_default_values_preserved(migration_context: tuple[Engine, Config]) -> None:
    """
    Test that default values work correctly before and after the migration.
    The migration drops and re-adds defaults, so we need to verify:
    1. The column has a DEFAULT after upgrade
    2. Empty arrays can be inserted and retrieved after upgrade
    3. The column has a DEFAULT after downgrade
    4. Empty arrays can be inserted and retrieved after downgrade
    """
    engine, alembic_config = migration_context

    def _verify_column_default(e: Engine, table: str) -> None:
        with e.connect() as conn:
            result = conn.execute(
                text("""
                SELECT column_default
                FROM information_schema.columns
                WHERE table_name = :table AND column_name = 'permissions'
            """),
                {"table": table},
            ).fetchone()
            assert result is not None, f"Column 'permissions' not found in {table}"
            assert result[0] is not None, f"Column {table}.permissions should have a default value"

    # Upgrade to the target migration
    command.upgrade(alembic_config, TARGET_REV)

    # Verify column has a default after upgrade
    _verify_column_default(engine, "team")

    # Test with explicit empty array after upgrade
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO team (name, created_at, updated_at) 
            VALUES ('test_default_team', NOW(), NOW())
        """)
        )

        result = conn.execute(
            text("""
            SELECT permissions::text[] FROM team WHERE name = 'test_default_team'
        """)
        ).fetchone()

        assert result is not None
        assert result[0] == []

        conn.execute(text("DELETE FROM team WHERE name = 'test_default_team'"))

    # Downgrade and test defaults still work
    command.downgrade(alembic_config, PREVIOUS_REV)

    # Verify column has a default after downgrade
    _verify_column_default(engine, "team")

    # Test with default insertion after downgrade
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO team (name, created_at, updated_at) 
            VALUES ('test_default_team_2', NOW(), NOW())
        """)
        )

        result = conn.execute(
            text("""
            SELECT permissions::text[] FROM team WHERE name = 'test_default_team_2'
        """)
        ).fetchone()

        assert result is not None
        assert result[0] == []
