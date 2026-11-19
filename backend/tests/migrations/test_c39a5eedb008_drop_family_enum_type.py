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

from collections.abc import Generator
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, make_url, text
from sqlalchemy_utils import create_database, drop_database  # type: ignore[import-untyped]

PREVIOUS_REV = "ad7acb807c63"
TARGET_REV = "c39a5eedb008"


@pytest.fixture
def migration_context(db_url: str) -> Generator[tuple[Engine, Config], None, None]:
    url = make_url(db_url).set(database=f"test_drop_family_enum_{uuid4().hex}")
    create_database(url)
    engine = create_engine(url)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url.render_as_string(hide_password=False))
    try:
        command.upgrade(config, PREVIOUS_REV)
        yield engine, config
    finally:
        engine.dispose()
        drop_database(url)


def _family_enum_labels(engine: Engine) -> list[str]:
    with engine.connect() as connection:
        return list(connection.scalars(text("SELECT unnest(enum_range(NULL::familyname))::text")))


def _family_enum_exists(engine: Engine) -> bool:
    with engine.connect() as connection:
        return connection.scalar(text("SELECT to_regtype('familyname') IS NOT NULL"))


def test_drops_and_restores_family_enum(migration_context: tuple[Engine, Config]) -> None:
    engine, config = migration_context
    assert _family_enum_exists(engine)

    command.upgrade(config, TARGET_REV)
    assert not _family_enum_exists(engine)

    command.downgrade(config, PREVIOUS_REV)
    assert _family_enum_labels(engine) == ["snap", "deb", "charm", "image", "solution"]
