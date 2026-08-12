# Copyright 2023 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from test_observer.data_access import Base
from test_observer.data_access.setup import DB_URL

# for 'autogenerate' support
target_metadata = Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Note: transitional expand/contract exclusions
# `alembic check` complains that the ORM models don't reference legacy solution-
# specific fields that were replaced by the `attributes` field. This happens
# because we are doing expand/contract migrations (for two separate releases);
# the following release will remove these exceptions.
_EXPAND_CONTRACT_IGNORED_TABLES: set[str] = {"artefact_bundled_builds_association"}
_EXPAND_CONTRACT_IGNORED_COLUMNS: set[tuple[str, str]] = {("artefact", "bundled_builds_hash")}
_EXPAND_CONTRACT_IGNORED_INDEXES: set[str] = {"unique_solution"}


def include_object(object, name, type_, reflected, compare_to):  # noqa: ANN001, ANN201, ARG001
    if type_ == "table" and name in _EXPAND_CONTRACT_IGNORED_TABLES:
        return False
    if type_ == "column":
        table_name = object.table.name if object.table is not None else None
        if (table_name, name) in _EXPAND_CONTRACT_IGNORED_COLUMNS:
            return False
    return not (type_ == "index" and name in _EXPAND_CONTRACT_IGNORED_INDEXES)


# Don't overwrite value if set by tests
if config.get_main_option("sqlalchemy.url") is None:
    config.set_main_option("sqlalchemy.url", DB_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            transaction_per_migration=True,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
