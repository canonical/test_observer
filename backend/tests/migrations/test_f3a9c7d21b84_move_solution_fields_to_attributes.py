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

"""Tests for moving the solution-specific bundled build fields into attributes.

This migration backfills ``attributes`` from the legacy solution-specific data,
swaps the ``unique_solution`` index to ``(name, version)`` and drops
``artefact.bundled_builds_hash`` and ``artefact_bundled_builds_association``.

``PREVIOUS_REV`` is the revision before this migration, where the ``attributes``
column already exists (added but not yet backfilled) alongside the legacy
``bundled_builds_hash`` column and association table.
"""

from collections.abc import Generator
from urllib.parse import urlparse, urlunparse

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import Connection
from sqlalchemy_utils import create_database, database_exists, drop_database  # type: ignore[import-untyped]

# The revision before this migration (attributes column present but not backfilled,
# legacy column/table still present).
PREVIOUS_REV = "a2cce585712b"
# The migration under test (backfills, drops old column/table, swaps index).
TARGET_REV = "f3a9c7d21b84"


@pytest.fixture
def migration_context(db_url: str) -> Generator[tuple[Engine, Config], None, None]:
    parsed = urlparse(db_url)
    test_db_url = urlunparse(
        (parsed.scheme, parsed.netloc, "/test_migration_move_solution", parsed.params, parsed.query, parsed.fragment)
    )

    if database_exists(test_db_url):
        drop_database(test_db_url)

    create_database(test_db_url)

    engine: Engine | None = None
    try:
        engine = create_engine(test_db_url)
        alembic_config = Config("alembic.ini")
        alembic_config.set_main_option("sqlalchemy.url", test_db_url)

        yield engine, alembic_config
    finally:
        if engine is not None:
            engine.dispose()
        if database_exists(test_db_url):
            drop_database(test_db_url)


def _insert_legacy_artefact(
    conn: Connection,
    name: str,
    bundled_builds_hash: str | None = None,
    version: str = "1.0",
    track: str = "latest",
    source: str = "source",
    stage: str = "stable",
) -> int:
    """Insert a solution artefact at the previous revision, where both the ``attributes``
    column and the legacy ``bundled_builds_hash`` column exist. ``attributes`` is left at
    its server default ({}) to simulate rows written before the backfill."""
    result = conn.execute(
        text("""
            INSERT INTO artefact (
                name, version, stage, family, status, archived, bug_link, comment,
                store, branch, track, series, repo, source, os, release, sha256, owner, image_url,
                created_at, updated_at, bundled_builds_hash
            )
            VALUES (
                :name, :version, :stage, 'solution', 'UNDECIDED', false, '', '',
                '', '', :track, '', '', :source, '', '', '', '', '',
                NOW(), NOW(), :bundled_builds_hash
            )
            RETURNING id
            """),
        {
            "name": name,
            "version": version,
            "stage": stage,
            "track": track,
            "source": source,
            "bundled_builds_hash": bundled_builds_hash,
        },
    )
    return result.scalar_one()


def _insert_artefact(
    conn: Connection,
    name: str,
    attributes: str = "{}",
    version: str = "1.0",
    track: str = "latest",
    source: str = "source",
    stage: str = "stable",
) -> int:
    """Insert a solution artefact at the target revision, where only the ``attributes``
    column exists (``bundled_builds_hash`` has been dropped)."""
    result = conn.execute(
        text("""
            INSERT INTO artefact (
                name, version, stage, family, status, archived, bug_link, comment,
                store, branch, track, series, repo, source, os, release, sha256, owner, image_url,
                created_at, updated_at, attributes
            )
            VALUES (
                :name, :version, :stage, 'solution', 'UNDECIDED', false, '', '',
                '', '', :track, '', '', :source, '', '', '', '', '',
                NOW(), NOW(), CAST(:attributes AS jsonb)
            )
            RETURNING id
            """),
        {
            "name": name,
            "version": version,
            "stage": stage,
            "track": track,
            "source": source,
            "attributes": attributes,
        },
    )
    return result.scalar_one()


def _insert_artefact_build(conn: Connection, artefact_id: int, architecture: str = "amd64") -> int:
    result = conn.execute(
        text("""
            INSERT INTO artefact_build (architecture, revision, artefact_id, created_at, updated_at)
            VALUES (:architecture, NULL, :artefact_id, NOW(), NOW())
            RETURNING id
            """),
        {"architecture": architecture, "artefact_id": artefact_id},
    )
    return result.scalar_one()


def _insert_association(conn: Connection, artefact_id: int, artefact_build_id: int) -> None:
    conn.execute(
        text("""
            INSERT INTO artefact_bundled_builds_association (artefact_id, artefact_build_id)
            VALUES (:artefact_id, :artefact_build_id)
            """),
        {"artefact_id": artefact_id, "artefact_build_id": artefact_build_id},
    )


def _attribute_text(engine: Engine, artefact_id: int, key: str) -> str | None:
    with engine.connect() as conn:
        return conn.execute(
            text("SELECT attributes::jsonb ->> :key FROM artefact WHERE id = :artefact_id"),
            {"artefact_id": artefact_id, "key": key},
        ).scalar_one()


def _bundled_build_ids(engine: Engine, artefact_id: int) -> list[int]:
    with engine.connect() as conn:
        return list(
            conn.execute(
                text("""
                    SELECT jsonb_array_elements_text(attributes::jsonb -> 'bundled_builds')::int
                    FROM artefact
                    WHERE id = :artefact_id
                    """),
                {"artefact_id": artefact_id},
            ).scalars()
        )


def test_upgrade_backfills_legacy_data_before_dropping(migration_context: tuple[Engine, Config]) -> None:
    """A row with legacy columns set and attributes still empty must be copied into
    attributes before the columns are dropped."""
    engine, alembic_config = migration_context
    command.upgrade(alembic_config, PREVIOUS_REV)
    with engine.begin() as conn:
        artefact_id = _insert_legacy_artefact(conn, "solution-leftover", bundled_builds_hash="hash-value")
        build_id = _insert_artefact_build(conn, artefact_id)
        _insert_association(conn, artefact_id, build_id)

    command.upgrade(alembic_config, TARGET_REV)

    assert _attribute_text(engine, artefact_id, "bundled_builds_hash") == "hash-value"
    assert _bundled_build_ids(engine, artefact_id) == [build_id]


def test_downgrade_restores_empty_attributes(migration_context: tuple[Engine, Config]) -> None:
    engine, alembic_config = migration_context
    command.upgrade(alembic_config, TARGET_REV)
    with engine.begin() as conn:
        artefact_id = _insert_artefact(conn, "solution-downgrade-empty", attributes="{}")

    command.downgrade(alembic_config, PREVIOUS_REV)

    with engine.connect() as conn:
        bundled_hash = conn.execute(
            text("SELECT bundled_builds_hash FROM artefact WHERE id = :id"),
            {"id": artefact_id},
        ).scalar_one()
        association_count = conn.execute(
            text("SELECT count(*) FROM artefact_bundled_builds_association WHERE artefact_id = :id"),
            {"id": artefact_id},
        ).scalar_one()
    assert bundled_hash is None
    assert association_count == 0


def test_downgrade_restores_hash_and_associations(migration_context: tuple[Engine, Config]) -> None:
    engine, alembic_config = migration_context
    command.upgrade(alembic_config, TARGET_REV)
    with engine.begin() as conn:
        artefact_id = _insert_artefact(conn, "solution-downgrade-both", attributes="{}")
        first_build_id = _insert_artefact_build(conn, artefact_id, architecture="amd64")
        second_build_id = _insert_artefact_build(conn, artefact_id, architecture="arm64")
        conn.execute(
            text("""
                UPDATE artefact
                SET attributes = jsonb_build_object(
                    'bundled_builds_hash', 'restored-hash',
                    'bundled_builds', jsonb_build_array(CAST(:first_build_id AS int), CAST(:second_build_id AS int))
                )
                WHERE id = :artefact_id
                """),
            {
                "artefact_id": artefact_id,
                "first_build_id": first_build_id,
                "second_build_id": second_build_id,
            },
        )

    command.downgrade(alembic_config, PREVIOUS_REV)

    with engine.connect() as conn:
        bundled_hash = conn.execute(
            text("SELECT bundled_builds_hash FROM artefact WHERE id = :id"),
            {"id": artefact_id},
        ).scalar_one()
        association_ids = list(
            conn.execute(
                text("""
                    SELECT artefact_build_id
                    FROM artefact_bundled_builds_association
                    WHERE artefact_id = :id
                    ORDER BY artefact_build_id
                    """),
                {"id": artefact_id},
            ).scalars()
        )
    assert bundled_hash == "restored-hash"
    assert association_ids == [first_build_id, second_build_id]


def test_downgrade_tolerates_malformed_bundled_builds(migration_context: tuple[Engine, Config]) -> None:
    """``attributes`` is writable via the API and is not schema-validated, so ``bundled_builds`` can
    hold arbitrary JSON (a non-array value, non-numeric elements, or unknown build ids). The
    downgrade must not blow up with a Postgres JSON/cast/FK error - it should skip invalid data and
    still restore the valid parts, so rollback is always possible."""
    engine, alembic_config = migration_context
    command.upgrade(alembic_config, TARGET_REV)
    with engine.begin() as conn:
        # A real build so we can prove valid ids are still restored alongside the bad ones.
        valid_artefact_id = _insert_artefact(conn, "solution-valid", attributes="{}")
        valid_build_id = _insert_artefact_build(conn, valid_artefact_id)
        conn.execute(
            text("""
                UPDATE artefact
                SET attributes = jsonb_build_object(
                    'bundled_builds_hash', 'keep-hash',
                    'bundled_builds', jsonb_build_array(CAST(:valid_build_id AS int))
                )
                WHERE id = :artefact_id
                """),
            {"artefact_id": valid_artefact_id, "valid_build_id": valid_build_id},
        )

        # bundled_builds is a scalar string, not an array -> jsonb_array_elements_text fails.
        non_array_id = _insert_artefact(conn, "solution-non-array", attributes='{"bundled_builds": "not-an-array"}')
        # bundled_builds contains a non-numeric element -> ::int cast fails.
        non_numeric_id = _insert_artefact(
            conn, "solution-non-numeric", attributes='{"bundled_builds": ["not-a-number"]}'
        )
        # bundled_builds references a build id that does not exist -> FK violation.
        unknown_build_id = _insert_artefact(
            conn, "solution-unknown-build", attributes='{"bundled_builds": [999999999]}'
        )

    # Raises a DatabaseError without the guards; with them it should complete cleanly.
    command.downgrade(alembic_config, PREVIOUS_REV)

    with engine.connect() as conn:
        # Valid data is still restored.
        assert (
            conn.execute(
                text("SELECT bundled_builds_hash FROM artefact WHERE id = :id"), {"id": valid_artefact_id}
            ).scalar_one()
            == "keep-hash"
        )
        assert list(
            conn.execute(
                text("SELECT artefact_build_id FROM artefact_bundled_builds_association WHERE artefact_id = :id"),
                {"id": valid_artefact_id},
            ).scalars()
        ) == [valid_build_id]

        # Malformed entries produce no association rows rather than aborting the whole downgrade.
        for bad_id in (non_array_id, non_numeric_id, unknown_build_id):
            assert (
                conn.execute(
                    text("SELECT count(*) FROM artefact_bundled_builds_association WHERE artefact_id = :id"),
                    {"id": bad_id},
                ).scalar_one()
                == 0
            )


def test_upgrade_fails_fast_on_duplicate_name_and_version(migration_context: tuple[Engine, Config]) -> None:
    """The previous-revision schema still allows several solutions sharing (name, version) as long as
    track/source differ; the upgrade must refuse to create the tighter (name, version) unique index
    rather than fail with an opaque database error, and must not partially apply."""
    engine, alembic_config = migration_context
    command.upgrade(alembic_config, PREVIOUS_REV)
    with engine.begin() as conn:
        _insert_legacy_artefact(conn, "dup-solution", version="1.0", track="track-a", source="source-a")
        _insert_legacy_artefact(conn, "dup-solution", version="1.0", track="track-b", source="source-b")

    with pytest.raises(RuntimeError, match="Cannot create unique index"):
        command.upgrade(alembic_config, TARGET_REV)

    # The failed migration must not have dropped the legacy column.
    with engine.connect() as conn:
        bundled_hash_column = conn.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'artefact' AND column_name = 'bundled_builds_hash'
                """)
        ).fetchone()
    assert bundled_hash_column is not None


def test_downgrade_fails_fast_on_duplicate_widened_key(migration_context: tuple[Engine, Config]) -> None:
    """Defends the downgrade's wider unique index the same way, in case data ever ends up violating
    it (e.g. the (name, version) index was bypassed or dropped out-of-band)."""
    engine, alembic_config = migration_context
    command.upgrade(alembic_config, TARGET_REV)
    with engine.begin() as conn:
        conn.execute(text("DROP INDEX unique_solution"))
        _insert_artefact(conn, "dup-solution", attributes='{"bundled_builds_hash": "hash-x"}')
        _insert_artefact(conn, "dup-solution", attributes='{"bundled_builds_hash": "hash-x"}')

    with pytest.raises(RuntimeError, match="Cannot create unique index"):
        command.downgrade(alembic_config, PREVIOUS_REV)


def test_upgrade_schema_changes(migration_context: tuple[Engine, Config]) -> None:
    engine, alembic_config = migration_context
    command.upgrade(alembic_config, TARGET_REV)

    with engine.connect() as conn:
        attributes_column = conn.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'artefact' AND column_name = 'attributes'
                """)
        ).fetchone()
        association_table = conn.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name = 'artefact_bundled_builds_association'
                """)
        ).fetchone()
        bundled_hash_column = conn.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'artefact' AND column_name = 'bundled_builds_hash'
                """)
        ).fetchone()

    assert attributes_column is not None
    assert association_table is None
    assert bundled_hash_column is None


def test_downgrade_schema_changes(migration_context: tuple[Engine, Config]) -> None:
    engine, alembic_config = migration_context
    command.upgrade(alembic_config, TARGET_REV)
    command.downgrade(alembic_config, PREVIOUS_REV)

    with engine.connect() as conn:
        attributes_column = conn.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'artefact' AND column_name = 'attributes'
                """)
        ).fetchone()
        association_table = conn.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name = 'artefact_bundled_builds_association'
                """)
        ).fetchone()
        bundled_hash_column = conn.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'artefact' AND column_name = 'bundled_builds_hash'
                """)
        ).fetchone()

    # Downgrading restores the legacy schema while keeping the attributes column
    # (attributes predates this migration).
    assert attributes_column is not None
    assert association_table is not None
    assert bundled_hash_column is not None
