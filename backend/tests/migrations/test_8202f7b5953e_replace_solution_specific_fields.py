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

"""Tests for replacing bundled build fields with generic artefact attributes."""

from collections.abc import Generator
from urllib.parse import urlparse, urlunparse

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import Connection
from sqlalchemy_utils import create_database, database_exists, drop_database  # type: ignore[import-untyped]

PREVIOUS_REV = "eba1d1c92dba"
TARGET_REV = "8202f7b5953e"


@pytest.fixture
def migration_context(db_url: str) -> Generator[tuple[Engine, Config], None, None]:
    parsed = urlparse(db_url)
    test_db_url = urlunparse(
        (parsed.scheme, parsed.netloc, "/test_migration_solution_attrs", parsed.params, parsed.query, parsed.fragment)
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


def _insert_artefact(
    conn: Connection,
    name: str,
    bundled_builds_hash: str | None = None,
    attributes: str | None = None,
    version: str = "1.0",
    track: str = "latest",
    source: str = "source",
    stage: str = "stable",
) -> int:
    optional_column = ", attributes" if attributes is not None else ", bundled_builds_hash"
    optional_value = ", CAST(:attributes AS jsonb)" if attributes is not None else ", :bundled_builds_hash"
    result = conn.execute(
        text(f"""
            INSERT INTO artefact (
                name, version, stage, family, status, archived, bug_link, comment,
                store, branch, track, series, repo, source, os, release, sha256, owner, image_url,
                created_at, updated_at{optional_column}
            )
            VALUES (
                :name, :version, :stage, 'solution', 'UNDECIDED', false, '', '',
                '', '', :track, '', '', :source, '', '', '', '', '',
                NOW(), NOW(){optional_value}
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


def _attribute_key_exists(engine: Engine, artefact_id: int, key: str) -> bool:
    with engine.connect() as conn:
        return conn.execute(
            text("SELECT attributes::jsonb ? :key FROM artefact WHERE id = :artefact_id"),
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


def test_upgrade_preserves_empty_attributes(migration_context: tuple[Engine, Config]) -> None:
    engine, alembic_config = migration_context
    command.upgrade(alembic_config, PREVIOUS_REV)
    with engine.begin() as conn:
        artefact_id = _insert_artefact(conn, "solution-empty")

    command.upgrade(alembic_config, TARGET_REV)

    with engine.connect() as conn:
        assert (
            conn.execute(
                text("SELECT attributes::jsonb FROM artefact WHERE id = :id"), {"id": artefact_id}
            ).scalar_one()
            == {}
        )


def test_upgrade_copies_hash_and_associations(migration_context: tuple[Engine, Config]) -> None:
    engine, alembic_config = migration_context
    command.upgrade(alembic_config, PREVIOUS_REV)
    with engine.begin() as conn:
        artefact_id = _insert_artefact(conn, "solution-with-both", bundled_builds_hash="hash-value")
        build_id = _insert_artefact_build(conn, artefact_id)
        _insert_association(conn, artefact_id, build_id)

    command.upgrade(alembic_config, TARGET_REV)

    assert _attribute_text(engine, artefact_id, "bundled_builds_hash") == "hash-value"
    assert _bundled_build_ids(engine, artefact_id) == [build_id]


def test_upgrade_copies_only_hash_when_no_associations(migration_context: tuple[Engine, Config]) -> None:
    engine, alembic_config = migration_context
    command.upgrade(alembic_config, PREVIOUS_REV)
    with engine.begin() as conn:
        artefact_id = _insert_artefact(conn, "solution-with-hash", bundled_builds_hash="hash-only")

    command.upgrade(alembic_config, TARGET_REV)

    assert _attribute_text(engine, artefact_id, "bundled_builds_hash") == "hash-only"
    assert not _attribute_key_exists(engine, artefact_id, "bundled_builds")


def test_upgrade_copies_only_associations_when_hash_null(migration_context: tuple[Engine, Config]) -> None:
    engine, alembic_config = migration_context
    command.upgrade(alembic_config, PREVIOUS_REV)
    with engine.begin() as conn:
        artefact_id = _insert_artefact(conn, "solution-with-assoc")
        build_id = _insert_artefact_build(conn, artefact_id)
        _insert_association(conn, artefact_id, build_id)

    command.upgrade(alembic_config, TARGET_REV)

    assert not _attribute_key_exists(engine, artefact_id, "bundled_builds_hash")
    assert _bundled_build_ids(engine, artefact_id) == [build_id]


def test_upgrade_copies_multiple_bundled_builds_in_ascending_order(migration_context: tuple[Engine, Config]) -> None:
    engine, alembic_config = migration_context
    command.upgrade(alembic_config, PREVIOUS_REV)
    with engine.begin() as conn:
        artefact_id = _insert_artefact(conn, "solution-with-many")
        first_build_id = _insert_artefact_build(conn, artefact_id, architecture="amd64")
        second_build_id = _insert_artefact_build(conn, artefact_id, architecture="arm64")
        _insert_association(conn, artefact_id, second_build_id)
        _insert_association(conn, artefact_id, first_build_id)

    command.upgrade(alembic_config, TARGET_REV)

    assert _bundled_build_ids(engine, artefact_id) == [first_build_id, second_build_id]


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


def test_upgrade_fails_fast_on_duplicate_name_and_version(migration_context: tuple[Engine, Config]) -> None:
    """Pre-migration schema allows several solutions sharing (name, version) as long as track/source
    differ; the upgrade must refuse to create the tighter (name, version) unique index rather than
    fail with an opaque database error."""
    engine, alembic_config = migration_context
    command.upgrade(alembic_config, PREVIOUS_REV)
    with engine.begin() as conn:
        _insert_artefact(conn, "dup-solution", version="1.0", track="track-a", source="source-a")
        _insert_artefact(conn, "dup-solution", version="1.0", track="track-b", source="source-b")

    with pytest.raises(RuntimeError, match="Cannot create unique index"):
        command.upgrade(alembic_config, TARGET_REV)

    # The failed migration must not have partially applied its schema changes.
    with engine.connect() as conn:
        attributes_column = conn.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'artefact' AND column_name = 'attributes'
                """)
        ).fetchone()
    assert attributes_column is None


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
                SELECT is_nullable, column_default
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
    assert attributes_column[0] == "NO"
    assert "'{}'" in attributes_column[1]
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

    assert attributes_column is None
    assert association_table is not None
    assert bundled_hash_column is not None
