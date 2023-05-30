# Copyright 2023 Canonical Ltd.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Written by:
#        Nadzeya Hutsko <nadzeya.hutsko@canonical.com>
#        Omar Selo <omar.selo@canonical.com>
"""Fixtures for testing"""


import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database
from test_observer.data_access import Base
from test_observer.data_access.models import Artefact, Stage
from test_observer.main import app, get_db


@pytest.fixture(scope="session")
def db_engine():
    db_uri = "postgresql+pg8000://postgres:password@test-observer-db:5432/test"

    if not database_exists(db_uri):
        create_database(db_uri)

    engine = create_engine(db_uri)

    alembic_config = Config("alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", db_uri)
    command.upgrade(alembic_config, "head")

    yield engine

    Base.metadata.drop_all(engine)
    engine.dispose()
    drop_database(db_uri)


@pytest.fixture(scope="function")
def db_session(db_engine: Engine):
    connection = db_engine.connect()
    # Start transaction and not commit it to rollback automatically
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()

    yield session

    session.close()
    transaction.close()
    connection.close()


@pytest.fixture(scope="function")
def test_client(db_session: Session) -> TestClient:
    """Create a test http client"""
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)
