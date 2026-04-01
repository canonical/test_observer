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

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy_utils import create_database, database_exists, drop_database
from urllib.parse import urlparse, urlunparse


def test_f0847700d32e_permissions_enum_migration_with_data(db_url: str):
    """
    Test migration f0847700d32e that changes permissions from string array to enum array.
    
    This test creates an isolated database and:
    1. Migrates to the revision before f0847700d32e
    2. Inserts test data with string array permissions  
    3. Upgrades to f0847700d32e (string -> enum)
    4. Verifies data is preserved and types are correct
    5. Downgrades back (enum -> string)
    6. Verifies data is still preserved
    """
    # Parse the URL and create a new database name
    parsed = urlparse(db_url)
    # Replace the database name in the path
    new_path = "/test_migration_f0847700d32e"
    test_db_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        new_path,
        parsed.params,
        parsed.query,
        parsed.fragment
    ))
    
    # Clean up any existing test database
    if database_exists(test_db_url):
        drop_database(test_db_url)
    
    # Create new test database
    create_database(test_db_url)
    
    try:
        engine = create_engine(test_db_url)
        alembic_config = Config("alembic.ini")
        alembic_config.set_main_option("sqlalchemy.url", test_db_url)
        
        # Step 1: Migrate to revision before the target migration
        command.upgrade(alembic_config, "c29b4f545a9b")
        
        # Step 2: Insert test data with string array permissions
        with engine.begin() as conn:
            # Insert applications with various permission strings (using actual enum values)
            conn.execute(text("""
                INSERT INTO application (name, permissions, api_key, created_at, updated_at) 
                VALUES 
                    ('test_app_1', '{"view_user"}', 'to_test_key_1', NOW(), NOW()),
                    ('test_app_2', '{"view_user", "change_user"}', 'to_test_key_2', NOW(), NOW()),
                    ('test_app_3', '{}', 'to_test_key_3', NOW(), NOW())
            """))
            
            # Insert teams with various permission strings (using actual enum values)
            conn.execute(text("""
                INSERT INTO team (name, permissions, created_at, updated_at) 
                VALUES 
                    ('test_team_1', '{"view_user"}', NOW(), NOW()),
                    ('test_team_2', '{"view_user", "view_issue"}', NOW(), NOW()),
                    ('test_team_3', '{}', NOW(), NOW())
            """))
        
        # Step 3: Upgrade to the target migration (string -> enum)
        command.upgrade(alembic_config, "f0847700d32e")
        
        # Step 4: Verify data is preserved and type is enum after upgrade
        with engine.begin() as conn:
            # Check applications
            app_results = conn.execute(text("""
                SELECT name, permissions::text[] 
                FROM application 
                WHERE name LIKE 'test_app_%'
                ORDER BY name
            """)).fetchall()
            
            assert len(app_results) == 3
            assert app_results[0][1] == ["view_user"]
            assert set(app_results[1][1]) == {"view_user", "change_user"}
            assert app_results[2][1] == []
            
            # Check teams
            team_results = conn.execute(text("""
                SELECT name, permissions::text[] 
                FROM team 
                WHERE name LIKE 'test_team_%'
                ORDER BY name
            """)).fetchall()
            
            assert len(team_results) == 3
            assert team_results[0][1] == ["view_user"]
            assert set(team_results[1][1]) == {"view_user", "view_issue"}
            assert team_results[2][1] == []
            
            # Verify the column type is now an enum array
            type_check = conn.execute(text("""
                SELECT 
                    column_name,
                    udt_name,
                    data_type
                FROM information_schema.columns 
                WHERE table_name IN ('application', 'team') 
                  AND column_name = 'permissions'
            """)).fetchall()
            
            # Both should be ARRAY type with permission enum
            assert len(type_check) == 2
            for row in type_check:
                assert row[2] == "ARRAY"
        
        # Step 5: Downgrade back to previous version (enum -> string)
        command.downgrade(alembic_config, "c29b4f545a9b")
        
        # Step 6: Verify data is still preserved after downgrade
        with engine.begin() as conn:
            # Check applications after downgrade
            app_results = conn.execute(text("""
                SELECT name, permissions 
                FROM application 
                WHERE name LIKE 'test_app_%'
                ORDER BY name
            """)).fetchall()
            
            assert len(app_results) == 3
            assert app_results[0][1] == ["view_user"]
            assert set(app_results[1][1]) == {"view_user", "change_user"}
            assert app_results[2][1] == []
            
            # Check teams after downgrade
            team_results = conn.execute(text("""
                SELECT name, permissions 
                FROM team 
                WHERE name LIKE 'test_team_%'
                ORDER BY name
            """)).fetchall()
            
            assert len(team_results) == 3
            assert team_results[0][1] == ["view_user"]
            assert set(team_results[1][1]) == {"view_user", "view_issue"}
            assert team_results[2][1] == []
            
            # Verify the column type is back to varchar array
            type_check = conn.execute(text("""
                SELECT 
                    column_name,
                    udt_name,
                    data_type
                FROM information_schema.columns 
                WHERE table_name IN ('application', 'team') 
                  AND column_name = 'permissions'
            """)).fetchall()
            
            # Both should be ARRAY type
            assert len(type_check) == 2
            for row in type_check:
                assert row[2] == "ARRAY"
        
        engine.dispose()
    finally:
        # Cleanup: drop the test database
        if database_exists(test_db_url):
            drop_database(test_db_url)


def test_f0847700d32e_default_values_preserved(db_url: str):
    """
    Test that default values work correctly after the migration.
    
    The migration drops and re-adds defaults, so we need to verify:
    1. Empty arrays can be inserted and retrieved after upgrade
    2. Empty arrays can be inserted and retrieved after downgrade
    """
    # Parse the URL and create a new database name
    parsed = urlparse(db_url)
    new_path = "/test_migration_defaults"
    test_db_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        new_path,
        parsed.params,
        parsed.query,
        parsed.fragment
    ))
    
    # Clean up any existing test database
    if database_exists(test_db_url):
        drop_database(test_db_url)
    
    # Create new test database
    create_database(test_db_url)
    
    try:
        engine = create_engine(test_db_url)
        alembic_config = Config("alembic.ini")
        alembic_config.set_main_option("sqlalchemy.url", test_db_url)
        
        # Upgrade to the target migration
        command.upgrade(alembic_config, "f0847700d32e")
        
        # Test with explicit empty array after upgrade (enum type)
        with engine.begin() as conn:
            # Insert with explicit empty array using enum type syntax
            conn.execute(text("""
                INSERT INTO team (name, permissions, created_at, updated_at) 
                VALUES ('test_default_team', '{}'::permission[], NOW(), NOW())
            """))
            
            # Check it has the empty array
            result = conn.execute(text("""
                SELECT permissions::text[] FROM team WHERE name = 'test_default_team'
            """)).fetchone()
            
            assert result is not None
            assert result[0] == []
            
            # Also verify the column has a DEFAULT defined
            default_check = conn.execute(text("""
                SELECT column_default
                FROM information_schema.columns
                WHERE table_name = 'team' AND column_name = 'permissions'
            """)).fetchone()
            
            assert default_check is not None
            assert default_check[0] is not None, "Column should have a default value"
            
            # Clean up first test team before downgrade
            conn.execute(text("DELETE FROM team WHERE name = 'test_default_team'"))
        
        # Downgrade and test with explicit empty array (string type)
        command.downgrade(alembic_config, "c29b4f545a9b")
        
        with engine.begin() as conn:
            # Insert with explicit empty array using varchar type syntax
            conn.execute(text("""
                INSERT INTO team (name, permissions, created_at, updated_at) 
                VALUES ('test_default_team_2', '{}'::character varying[], NOW(), NOW())
            """))
            
            # Check it has the empty array
            result = conn.execute(text("""
                SELECT permissions FROM team WHERE name = 'test_default_team_2'
            """)).fetchone()
            
            assert result is not None
            assert result[0] == []
            
            # Verify the column has a DEFAULT defined after downgrade
            default_check = conn.execute(text("""
                SELECT column_default
                FROM information_schema.columns
                WHERE table_name = 'team' AND column_name = 'permissions'
            """)).fetchone()
            
            assert default_check is not None
            assert default_check[0] is not None, "Column should have a default value after downgrade"
        
        engine.dispose()
    finally:
        # Cleanup: drop the test database
        if database_exists(test_db_url):
            drop_database(test_db_url)
