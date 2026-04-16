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

"""Tests for migration d9c144615947: Add all Artefact attributes to ArtefactMatchingRules"""

from collections.abc import Generator
from urllib.parse import urlparse, urlunparse

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy_utils import create_database, database_exists, drop_database  # type: ignore[import-untyped]

# Migration revision constants
PREVIOUS_REV = "f0847700d32e"
TARGET_REV = "d9c144615947"


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
        (parsed.scheme, parsed.netloc, "/test_migration_amr_attrs", parsed.params, parsed.query, parsed.fragment)
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


def test_upgrade_adds_new_columns_and_constraint(migration_context: tuple[Engine, Config]) -> None:
    """
    Test that upgrade correctly adds new columns and updates the unique constraint.

    This test:
    1. Migrates to the revision before TARGET_REV
    2. Upgrades to TARGET_REV
    3. Verifies that new columns exist
    4. Verifies that the new constraint is created
    """
    engine, alembic_config = migration_context

    # Step 1: Migrate to revision before the target migration
    command.upgrade(alembic_config, PREVIOUS_REV)

    # Step 2: Upgrade to the target migration
    command.upgrade(alembic_config, TARGET_REV)

    # Step 3: Verify new columns exist
    with engine.connect() as conn:
        result = conn.execute(
            text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'artefact_matching_rule'
            ORDER BY column_name
        """)
        ).fetchall()

        column_names = [row[0] for row in result]
        assert "store" in column_names
        assert "series" in column_names
        assert "os" in column_names
        assert "release" in column_names
        assert "owner" in column_names

    # Step 4: Verify new constraint exists
    with engine.connect() as conn:
        result = conn.execute(
            text("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'artefact_matching_rule' 
            AND constraint_type = 'UNIQUE'
        """)
        ).fetchall()

        constraint_names = [row[0] for row in result]
        assert "artefact_matching_rule_fields_from_artefact" in constraint_names


def test_downgrade_merges_duplicates_correctly(migration_context: tuple[Engine, Config]) -> None:
    """
    Test that downgrade correctly merges duplicate rules.

    This test:
    1. Migrates to TARGET_REV
    2. Inserts duplicate rules (same name, family, stage, track, branch but different new columns)
    3. Inserts teams associated with both rules
    4. Downgrades to PREVIOUS_REV
    5. Verifies duplicates are merged and teams are preserved
    """
    engine, alembic_config = migration_context

    # Step 1: Upgrade to target migration
    command.upgrade(alembic_config, TARGET_REV)

    # Step 2: Insert teams first
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO team (name, permissions, created_at, updated_at)
            VALUES 
                ('team_1', ARRAY[]::permission[], NOW(), NOW()),
                ('team_2', ARRAY[]::permission[], NOW(), NOW())
        """)
        )

    # Step 3: Insert duplicate rules with different new column values
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO artefact_matching_rule 
            (name, family, stage, track, branch, store, series, os, release, owner,
             created_at, updated_at)
            VALUES 
                ('rule_1', 'snap', 'candidate', 'stable', 'main', 'snapcraft',
                 'focal', 'x86_64', '20.04', 'owner1', NOW(), NOW()),
                ('rule_1', 'snap', 'candidate', 'stable', 'main', 'snapcraft2',
                 'jammy', 'arm64', '22.04', 'owner2', NOW(), NOW()),
                ('rule_1', 'snap', 'candidate', 'stable', 'main', 'snapcraft3',
                 'noble', 'ppc64el', '24.04', 'owner3', NOW(), NOW())
        """)
        )

        # Get the rule IDs
        rules = conn.execute(
            text("""
            SELECT id, store FROM artefact_matching_rule 
            WHERE name = 'rule_1'
            ORDER BY id ASC
        """)
        ).fetchall()

        rule_ids = [row[0] for row in rules]

        # Assign teams to all rules
        for rule_id in rule_ids:
            # Assign team_1 to all rules (will need deduplication)
            conn.execute(
                text("""
                INSERT INTO artefact_matching_rule_team_association 
                (artefact_matching_rule_id, team_id)
                SELECT :rule_id, id FROM team WHERE name = 'team_1'
            """),
                {"rule_id": rule_id},
            )

        # Assign team_2 only to rule 1 and 2
        for rule_id, _ in rule_ids[:2]:
            conn.execute(
                text("""
                INSERT INTO artefact_matching_rule_team_association 
                (artefact_matching_rule_id, team_id)
                SELECT :rule_id, id FROM team WHERE name = 'team_2'
            """),
                {"rule_id": rule_id},
            )

    # Step 4: Downgrade to previous revision
    command.downgrade(alembic_config, PREVIOUS_REV)

    # Step 5: Verify duplicates are merged and teams are preserved
    with engine.connect() as conn:
        # Verify only one rule remains
        rules = conn.execute(
            text("""
            SELECT id FROM artefact_matching_rule 
            WHERE name = 'rule_1' AND family = 'snap' AND stage = 'candidate' 
            AND track = 'stable' AND branch = 'main'
        """)
        ).fetchall()

        assert len(rules) == 1, "Expected only one merged rule after downgrade"
        survivor_id = rules[0][0]

        # Verify survivor has both teams
        teams = conn.execute(
            text("""
            SELECT t.name FROM team t
            JOIN artefact_matching_rule_team_association amrta 
            ON t.id = amrta.team_id
            WHERE amrta.artefact_matching_rule_id = :survivor_id
            ORDER BY t.name
        """),
            {"survivor_id": survivor_id},
        ).fetchall()

        team_names = [row[0] for row in teams]
        assert "team_1" in team_names
        assert "team_2" in team_names
        assert len(team_names) == 2, f"Expected 2 teams, got {len(team_names)}"
