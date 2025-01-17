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


from os import environ

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy_utils import (  # type: ignore
    create_database,
    drop_database,
)

from test_observer.data_access.models import TestExecution
from test_observer.data_access.models_enums import StageName
from test_observer.data_access.setup import get_db
from test_observer.main import app
from tests.data_generator import DataGenerator


@pytest.fixture(scope="session")
def db_url():
    """
    Retrieves the database url from the environment variable TEST_DB_URL
    or creates a new database and returns the url
    """
    db_url = environ.get("TEST_DB_URL")
    if db_url:
        yield db_url
    else:
        db_url = "postgresql+pg8000://postgres:password@test-observer-db:5432/test"
        create_database(db_url)

        yield db_url

        drop_database(db_url)


@pytest.fixture(scope="session")
def db_engine(db_url: str):
    engine = create_engine(db_url)

    alembic_config = Config("alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_config, "head")

    yield engine

    command.downgrade(alembic_config, "base")
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine: Engine):
    connection = db_engine.connect()
    # Start transaction and not commit it to rollback automatically
    transaction = connection.begin()
    session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=connection,
        expire_on_commit=False,
    )()

    yield session

    session.close()
    transaction.close()
    connection.close()


@pytest.fixture(scope="function")
def test_client(db_session: Session) -> TestClient:
    """Create a test http client"""
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


@pytest.fixture
def generator(db_session: Session) -> DataGenerator:
    return DataGenerator(db_session)


@pytest.fixture
def test_execution(generator: DataGenerator) -> TestExecution:
    a = generator.gen_artefact(StageName.beta)
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment()
    te = generator.gen_test_execution(ab, e)
    return te
