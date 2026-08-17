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

"""Tests for backfilling artefact.attributes from legacy bundled build fields.

This data-only migration copies existing bundled build data into ``attributes``.
The old ``bundled_builds_hash`` column and ``artefact_bundled_builds_association``
table remain in place so old code keeps working during a rolling upgrade; they
are removed by a later migration.
"""

from collections.abc import Generator
from urllib.parse import urlparse, urlunparse

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import Connection
from sqlalchemy_utils import create_database, database_exists, drop_database  # type: ignore[import-untyped]

# Revision that adds the (empty) attributes column.
PREVIOUS_REV = "6e262c3c6c8f"
# Revision that backfills attributes from the legacy bundled build fields.
TARGET_REV = "d315c1f212b9"


@pytest.fixture
def migration_context(db_url: str) -> Generator[tuple[Engine, Config], None, None]:
    parsed = urlparse(db_url)
    test_db_url = urlunparse(
        (parsed.scheme, parsed.netloc, "/test_migration_backfill_attrs", parsed.params, parsed.query, parsed.fragment)
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


def test_upgrade_does_not_clobber_existing_attributes(migration_context: tuple[Engine, Config]) -> None:
    engine, alembic_config = migration_context
    command.upgrade(alembic_config, PREVIOUS_REV)
    with engine.begin() as conn:
        artefact_id = _insert_artefact(
            conn,
            "solution-write-both",
            attributes='{"track": "latest", "source": "source"}',
        )
        build_id = _insert_artefact_build(conn, artefact_id)
        _insert_association(conn, artefact_id, build_id)

    command.upgrade(alembic_config, TARGET_REV)

    assert _attribute_text(engine, artefact_id, "track") == "latest"
    assert _attribute_text(engine, artefact_id, "source") == "source"
    assert _bundled_build_ids(engine, artefact_id) == [build_id]


def test_upgrade_leaves_legacy_schema_in_place(migration_context: tuple[Engine, Config]) -> None:
    """The backfill migration must not remove the old column/table."""
    engine, alembic_config = migration_context
    command.upgrade(alembic_config, TARGET_REV)

    with engine.connect() as conn:
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

    assert association_table is not None
    assert bundled_hash_column is not None


def test_downgrade_is_a_noop_for_schema(migration_context: tuple[Engine, Config]) -> None:
    """Downgrading the data-only backfill leaves the schema untouched."""
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

    assert attributes_column is not None
