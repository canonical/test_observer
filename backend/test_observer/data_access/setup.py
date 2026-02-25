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

import os
import traceback
from os import environ
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, ExecutionContext
from sqlalchemy.engine.interfaces import DBAPICursor
from sqlalchemy.event import listens_for
from sqlalchemy.orm import sessionmaker

DEFAULT_DB_URL = "postgresql+pg8000://postgres:password@test-observer-db:5432/postgres"
DB_URL = environ.get("DB_URL", DEFAULT_DB_URL)

engine = create_engine(DB_URL, pool_size=45, max_overflow=45)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

DBAPIParameters = dict[Any, Any] | tuple[Any] | list[Any] | None


# https://docs.sqlalchemy.org/en/20/core/events.html#sqlalchemy.events.ConnectionEvents.before_cursor_execute
# retval=True is needed to actually modify the statement
@listens_for(engine, "before_cursor_execute", retval=True)
def tag_sql_with_origin(
    _conn: Connection,
    _cursor: DBAPICursor,
    statement: str,
    parameters: DBAPIParameters,
    _context: ExecutionContext,
    _executemany: bool,
) -> tuple[str, DBAPIParameters]:
    """
    This event listener tags each SQL statement with a comment
    containing the stack trace of where the query originated.
    """

    stack = traceback.extract_stack()

    origin = None
    # The last frame in the stack is this function, so we skip it.
    for frame in reversed(stack[:-1]):
        # We then look for the frame before this function that comes from our code
        if "test_observer" in frame.filename:
            origin = f"{os.path.basename(frame.filename)}:{frame.name}"
            break

    # There appear to be some calls to our engine directly from somewhere
    # in the SQLAlchemy/FastAPI/Pydantic pipeline,
    # so it is possible for origin to remain None.
    if origin:
        statement = f"/* Origin: {origin} */ " + statement

    return statement, parameters


# Dependency
def get_db():
    with SessionLocal() as db:
        yield db
