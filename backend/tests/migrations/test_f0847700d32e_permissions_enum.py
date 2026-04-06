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

"""Tests for database migrations"""

from collections.abc import Generator
from urllib.parse import urlparse, urlunparse

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy_utils import create_database, database_exists, drop_database  # type: ignore[import-untyped]

# Migration revision constants
PREVIOUS_REV = "c29b4f545a9b"
TARGET_REV = "f0847700d32e"

# Tables affected by this migration
TABLES_WITH_PERMISSIONS = ["application", "team"]


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
        (parsed.scheme, parsed.netloc, "/test_migration_perm_enum", parsed.params, parsed.query, parsed.fragment)
    )

    # Clean up any existing test database
    if database_exists(test_db_url):
        drop_database(test_db_url)

    # Create new test database
    create_database(test_db_url)

    try:
        # Initialize engine and alembic config
        engine = create_engine(test_db_url)
        alembic_config = Config("alembic.ini")
        alembic_config.set_main_option("sqlalchemy.url", test_db_url)

        yield engine, alembic_config

    finally:
        # Cleanup: dispose engine and drop database
        engine.dispose()
        if database_exists(test_db_url):
            drop_database(test_db_url)


def _insert_test_data(engine: Engine) -> None:
    """Insert test data with various permission configurations."""
    with engine.begin() as conn:
        # Insert applications with various permission strings
        conn.execute(
            text("""
            INSERT INTO application (name, permissions, api_key, created_at, updated_at) 
            VALUES 
                ('test_app_1', '{"view_user"}', 'to_test_key_1', NOW(), NOW()),
                ('test_app_2', '{"view_user", "change_user"}', 'to_test_key_2', NOW(), NOW()),
                ('test_app_3', '{}', 'to_test_key_3', NOW(), NOW())
        """)
        )

        # Insert teams with various permission strings
        conn.execute(
            text("""
            INSERT INTO team (name, permissions, created_at, updated_at) 
            VALUES 
                ('test_team_1', '{"view_user"}', NOW(), NOW()),
                ('test_team_2', '{"view_user", "view_issue"}', NOW(), NOW()),
                ('test_team_3', '{}', NOW(), NOW())
        """)
        )


def _verify_permissions_data(
    engine: Engine, table: str, expected_data: list[tuple[str, list[str]]], cast_to_text: bool = False
) -> None:
    """
    Verify permissions data in a given table.

    Args:
        engine: SQLAlchemy engine
        table: Table name to check
        expected_data: List of (name, permissions) tuples
        cast_to_text: Whether to cast permissions to text[] for comparison
    """
    with engine.connect() as conn:
        permissions_col = "permissions::text[]" if cast_to_text else "permissions"
        results = conn.execute(
            text(f"""
            SELECT name, {permissions_col} 
            FROM {table} 
            WHERE name LIKE 'test_%'
            ORDER BY name
        """)
        ).fetchall()

        assert len(results) == len(expected_data), f"Expected {len(expected_data)} rows in {table}"

        for result, (expected_name, expected_perms) in zip(results, expected_data, strict=False):
            assert result[0] == expected_name, f"Name mismatch in {table}"
            if len(expected_perms) > 1:
                # For multiple permissions, compare as sets (order doesn't matter)
                assert set(result[1]) == set(expected_perms), f"Permissions mismatch for {expected_name} in {table}"
            else:
                # For single or empty permissions, compare directly
                assert result[1] == expected_perms, f"Permissions mismatch for {expected_name} in {table}"


def _verify_column_type(engine: Engine, tables: list[str], expected_type: str = "ARRAY") -> None:
    """
    Verify the permissions column data type for given tables.

    Args:
        engine: SQLAlchemy engine
        tables: List of table names to check
        expected_type: Expected SQL data type
    """
    with engine.connect() as conn:
        for table in tables:
            result = conn.execute(
                text("""
                SELECT data_type
                FROM information_schema.columns 
                WHERE table_name = :table AND column_name = 'permissions'
            """),
                {"table": table},
            ).fetchone()

            assert result is not None, f"Column 'permissions' not found in {table}"
            assert result[0] == expected_type, f"Expected {expected_type} type for {table}.permissions"


def _verify_column_default(engine: Engine, table: str, should_have_default: bool = True) -> None:
    """
    Verify that the permissions column has a default value.

    Args:
        engine: SQLAlchemy engine
        table: Table name to check
        should_have_default: Whether a default should exist
    """
    with engine.connect() as conn:
        result = conn.execute(
            text("""
            SELECT column_default
            FROM information_schema.columns
            WHERE table_name = :table AND column_name = 'permissions'
        """),
            {"table": table},
        ).fetchone()

        assert result is not None, f"Column 'permissions' not found in {table}"

        if should_have_default:
            assert result[0] is not None, f"Column {table}.permissions should have a default value"
        else:
            assert result[0] is None, f"Column {table}.permissions should not have a default value"


def test_f0847700d32e_permissions_enum_migration_with_data(migration_context: tuple[Engine, Config]) -> None:
    """
    Test migration f0847700d32e that changes permissions from string array to enum array.

    This test:
    1. Migrates to the revision before TARGET_REV
    2. Inserts test data with string array permissions
    3. Upgrades to TARGET_REV (string -> enum)
    4. Verifies data is preserved and types are correct
    5. Downgrades back (enum -> string)
    6. Verifies data is still preserved
    """
    engine, alembic_config = migration_context

    # Expected data for verification
    expected_apps = [
        ("test_app_1", ["view_user"]),
        ("test_app_2", ["view_user", "change_user"]),
        ("test_app_3", []),
    ]
    expected_teams = [
        ("test_team_1", ["view_user"]),
        ("test_team_2", ["view_user", "view_issue"]),
        ("test_team_3", []),
    ]

    # Step 1: Migrate to revision before the target migration
    command.upgrade(alembic_config, PREVIOUS_REV)

    # Step 2: Insert test data with string array permissions
    _insert_test_data(engine)

    # Step 3: Upgrade to the target migration (string -> enum)
    command.upgrade(alembic_config, TARGET_REV)

    # Step 4: Verify data is preserved and type is enum after upgrade
    _verify_permissions_data(engine, "application", expected_apps, cast_to_text=True)
    _verify_permissions_data(engine, "team", expected_teams, cast_to_text=True)
    _verify_column_type(engine, TABLES_WITH_PERMISSIONS, expected_type="ARRAY")

    # Step 5: Downgrade back to previous version (enum -> string)
    command.downgrade(alembic_config, PREVIOUS_REV)

    # Step 6: Verify data is still preserved after downgrade
    _verify_permissions_data(engine, "application", expected_apps, cast_to_text=False)
    _verify_permissions_data(engine, "team", expected_teams, cast_to_text=False)
    _verify_column_type(engine, TABLES_WITH_PERMISSIONS, expected_type="ARRAY")


def test_f0847700d32e_default_values_preserved(migration_context: tuple[Engine, Config]) -> None:
    """
    Test that default values work correctly after the migration.

    The migration drops and re-adds defaults, so we need to verify:
    1. The column has a DEFAULT after upgrade
    2. Empty arrays can be inserted and retrieved after upgrade
    3. The column has a DEFAULT after downgrade
    4. Empty arrays can be inserted and retrieved after downgrade
    """
    engine, alembic_config = migration_context

    # Upgrade to the target migration
    command.upgrade(alembic_config, TARGET_REV)

    # Verify column has a default after upgrade
    _verify_column_default(engine, "team", should_have_default=True)

    # Test with explicit empty array after upgrade (enum type)
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO team (name, permissions, created_at, updated_at) 
            VALUES ('test_default_team', '{}'::permission[], NOW(), NOW())
        """)
        )

        result = conn.execute(
            text("""
            SELECT permissions::text[] FROM team WHERE name = 'test_default_team'
        """)
        ).fetchone()

        assert result is not None
        assert result[0] == []

        # Clean up
        conn.execute(text("DELETE FROM team WHERE name = 'test_default_team'"))

    # Downgrade and test defaults still work
    command.downgrade(alembic_config, PREVIOUS_REV)

    # Verify column has a default after downgrade
    _verify_column_default(engine, "team", should_have_default=True)

    # Test with explicit empty array after downgrade (string type)
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO team (name, permissions, created_at, updated_at) 
            VALUES ('test_default_team_2', '{}'::character varying[], NOW(), NOW())
        """)
        )

        result = conn.execute(
            text("""
            SELECT permissions FROM team WHERE name = 'test_default_team_2'
        """)
        ).fetchone()

        assert result is not None
        assert result[0] == []
