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
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database
from src.data_access import Base
from src.data_access.models import Artefact, Stage
from src.main import app, get_db


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


@pytest.fixture(scope="session")
def db_sessionmaker(db_engine) -> sessionmaker[Session]:
    return sessionmaker(autocommit=False, autoflush=False, bind=db_engine)


@pytest.fixture(scope="function")
def db_session(db_sessionmaker: sessionmaker[Session]):
    session = db_sessionmaker()
    yield session
    session.close()


@pytest.fixture(scope="session")
def test_client(db_sessionmaker: sessionmaker[Session]) -> TestClient:
    """Create a test http client"""

    def _get_db():
        session = db_sessionmaker()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _get_db
    return TestClient(app)


@pytest.fixture(scope="function")
def create_artefact(db_session: Session):
    created_artefacts = []

    def _create_artefact(stage_name: str, **kwargs):
        """Create a dummy artefact"""
        stage = db_session.query(Stage).filter(Stage.name == stage_name).first()
        artefact = Artefact(
            name=kwargs.get("name", ""),
            stage=stage,
            version=kwargs.get("version", "1.1.1"),
            source=kwargs.get("source", {}),
            artefact_group=None,
            is_archived=kwargs.get("is_archived", False),
        )
        db_session.add(artefact)
        db_session.commit()
        created_artefacts.append(artefact)
        return artefact

    yield _create_artefact

    for artefact in created_artefacts:
        db_session.delete(artefact)
    db_session.commit()
