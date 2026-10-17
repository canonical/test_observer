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

"""Tests that the Alembic advisory lock serialises concurrent migrations."""

import threading
import time
from collections.abc import Callable, Generator
from unittest.mock import patch
from urllib.parse import urlparse, urlunparse

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy_utils import create_database, database_exists, drop_database  # type: ignore[import-untyped]

from test_observer.common.constants import MIGRATION_LOCK_ID

WAIT_TIMEOUT = 30.0
BLOCKED_CHECK_SECONDS = 1.0

WAITING_ADVISORY_LOCKS = text(
    "SELECT count(*) FROM pg_locks "
    "WHERE locktype = 'advisory' AND NOT granted "
    "AND database = (SELECT oid FROM pg_database WHERE datname = current_database())"
)


@pytest.fixture
def migration_context(db_url: str) -> Generator[tuple[Engine, Config], None, None]:
    """Create an isolated, empty database for migration locking tests."""
    parsed = urlparse(db_url)
    test_db_url = urlunparse(
        (parsed.scheme, parsed.netloc, "/test_migration_lock", parsed.params, parsed.query, parsed.fragment)
    )

    if database_exists(test_db_url):
        drop_database(test_db_url)
    create_database(test_db_url)

    engine = create_engine(test_db_url)
    alembic_config = Config("alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", test_db_url)
    try:
        yield engine, alembic_config
    finally:
        engine.dispose()
        if database_exists(test_db_url):
            drop_database(test_db_url)


def _wait_until(condition: Callable[[], bool], description: str) -> None:
    deadline = time.monotonic() + WAIT_TIMEOUT
    while time.monotonic() < deadline:
        if condition():
            return
        time.sleep(0.05)
    pytest.fail(f"Timed out waiting for {description}")


def _upgrade_in_thread(config: Config, errors: list[BaseException]) -> threading.Thread:
    def run() -> None:
        try:
            command.upgrade(config, "heads")
        except BaseException as e:  # noqa: BLE001 - surfaced to the test thread
            errors.append(e)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread


def _is_at_heads(engine: Engine, config: Config) -> bool:
    if "alembic_version" not in inspect(engine).get_table_names():
        return False
    with engine.connect() as conn:
        current = {row[0] for row in conn.execute(text("SELECT version_num FROM alembic_version"))}
    return current == set(ScriptDirectory.from_config(config).get_heads())


def _is_lock_free(engine: Engine) -> bool:
    with engine.connect() as conn:
        acquired = conn.execute(text("SELECT pg_try_advisory_lock(:id)"), {"id": MIGRATION_LOCK_ID}).scalar_one()
        if acquired:
            conn.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": MIGRATION_LOCK_ID})
        conn.commit()
    return bool(acquired)


def _is_blocked_on_lock(engine: Engine) -> bool:
    with engine.connect() as conn:
        return conn.execute(WAITING_ADVISORY_LOCKS).scalar_one() > 0


def test_migration_waits_for_held_lock_then_proceeds(migration_context: tuple[Engine, Config]) -> None:
    engine, config = migration_context
    errors: list[BaseException] = []

    # GIVEN another migrating process holds the lock
    holder = engine.connect()
    holder.execute(text("SELECT pg_advisory_lock(:id)"), {"id": MIGRATION_LOCK_ID})
    holder.commit()
    try:
        # WHEN a migration starts
        thread = _upgrade_in_thread(config, errors)
        _wait_until(lambda: _is_blocked_on_lock(engine), "migration to block on the advisory lock")

        # THEN it makes no progress while the lock is held
        thread.join(timeout=BLOCKED_CHECK_SECONDS)
        assert thread.is_alive()
        assert "alembic_version" not in inspect(engine).get_table_names()
    finally:
        # WHEN the holder releases the lock
        holder.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": MIGRATION_LOCK_ID})
        holder.commit()
        holder.close()

    # THEN the waiting migration completes
    thread.join(timeout=WAIT_TIMEOUT)
    assert not thread.is_alive()
    assert errors == []
    assert _is_at_heads(engine, config)
    assert _is_lock_free(engine)


def _fail_migrations(*_args: object, **_kwargs: object) -> None:
    raise RuntimeError("boom")


def test_lock_is_released_after_failed_migration(migration_context: tuple[Engine, Config]) -> None:
    engine, config = migration_context

    # GIVEN a migration that fails after taking the lock
    with (
        patch("alembic.runtime.environment.EnvironmentContext.run_migrations", new=_fail_migrations),
        pytest.raises(RuntimeError, match="boom"),
    ):
        command.upgrade(config, "heads")

    # THEN the lock is free and a later migration is not blocked
    assert _is_lock_free(engine)
    command.upgrade(config, "heads")
    assert _is_at_heads(engine, config)


def test_waiting_migration_proceeds_after_holder_fails(migration_context: tuple[Engine, Config]) -> None:
    engine, config = migration_context
    errors: list[BaseException] = []

    # GIVEN a holder that takes the lock and then dies without unlocking
    holder = engine.connect()
    holder.execute(text("SELECT pg_advisory_lock(:id)"), {"id": MIGRATION_LOCK_ID})
    holder.commit()

    thread = _upgrade_in_thread(config, errors)
    _wait_until(lambda: _is_blocked_on_lock(engine), "migration to block on the advisory lock")

    # WHEN the holder's session ends (connection dropped)
    holder.invalidate()
    holder.close()

    # THEN the waiting migration acquires the lock and completes
    thread.join(timeout=WAIT_TIMEOUT)
    assert not thread.is_alive()
    assert errors == []
    assert _is_at_heads(engine, config)
