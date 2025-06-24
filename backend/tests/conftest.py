# Copyright (C) 2023 Canonical Ltd.
#
# This file is part of Test Observer Backend.
#
# Test Observer Backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# Test Observer Backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""Fixtures for testing"""

from os import environ

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
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


def _check_postgres_connection(host: str, port: int, user: str, password: str) -> bool:
    """Check if we can connect to PostgreSQL at the given host."""
    try:
        # Try to connect to the default 'postgres' database to test connectivity
        test_url = f"postgresql+pg8000://{user}:{password}@{host}:{port}/postgres"
        test_engine = create_engine(test_url, connect_args={"timeout": 2})
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        test_engine.dispose()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def db_url():
    """
    Retrieves the database url from the environment variable TEST_DB_URL
    or creates a new database and returns the url
    """
    # First priority: explicit TEST_DB_URL environment variable
    if db_url := environ.get("TEST_DB_URL"):
        yield db_url
        return

    # Database connection parameters
    db_params = {
        "user": "test_observer_user",
        "password": "test_observer_password",
        "database": "test",
        "port": 5432,
    }

    # Define potential database hosts in order of preference
    hosts = [
        "localhost",  # For running tests on host OS
        "test-observer-db",  # For running tests inside Docker
    ]

    # Find the first host that we can connect to
    selected_host = None
    for host in hosts:
        if _check_postgres_connection(
            host, db_params["port"], db_params["user"], db_params["password"]
        ):
            selected_host = host
            break

    if not selected_host:
        raise RuntimeError(
            "Could not connect to PostgreSQL. Make sure either:\n"
            "1. PostgreSQL is running on localhost:5432 (Docker Compose), or\n"
            "2. You're running tests inside Docker Compose, or\n"
            "3. Set TEST_DB_URL environment variable"
        )

    # Now create the test database
    db_url = f"postgresql+pg8000://{db_params['user']}:{db_params['password']}@{selected_host}:{db_params['port']}/{db_params['database']}"
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
