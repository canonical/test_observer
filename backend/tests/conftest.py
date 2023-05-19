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
"""Fixtures for testing"""


import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy_utils import database_exists, create_database, drop_database
from fastapi.testclient import TestClient
from src.main import app
from src.data_access import Base
from src.data_access.models import Family, Stage, Artefact


# Setup Test Database
SQLALCHEMY_DATABASE_URL = (
    "postgresql+pg8000://postgres:password@test-observer-db:5432/test"
)
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def seed_db(db_session: Session):
    """Populate database with fake data"""
    # Snap family
    family = Family(name="snap")
    db_session.add(family)
    # Edge stage
    stage = Stage(name="edge", family=family, position=10)
    db_session.add(stage)
    artefact = Artefact(
        name="core20", stage=stage, version="1.1.1", source={}, artefact_group=None
    )
    db_session.add(artefact)
    artefact = Artefact(
        name="docker",
        stage=stage,
        version="1.1.1",
        source={},
        artefact_group=None,
        is_archived=True,
    )
    db_session.add(artefact)
    # Beta stage
    stage = Stage(name="beta", family=family, position=20)
    db_session.add(stage)
    artefact = Artefact(
        name="core22", stage=stage, version="1.1.0", source={}, artefact_group=None
    )
    db_session.add(artefact)

    # Deb family
    family = Family(name="deb")
    db_session.add(family)
    # Proposed stage
    stage = Stage(name="proposed", family=family, position=10)
    db_session.add(stage)
    artefact = Artefact(
        name="jammy", stage=stage, version="2.1.1", source={}, artefact_group=None
    )
    db_session.add(artefact)
    # Updates stage
    stage = Stage(name="updates", family=family, position=10)
    db_session.add(stage)
    artefact = Artefact(
        name="raspi", stage=stage, version="2.1.0", source={}, artefact_group=None
    )
    db_session.add(artefact)
    db_session.commit()

    yield

    # Cleanup
    db_session.query(Artefact).delete()
    db_session.query(Stage).delete()
    db_session.query(Family).delete()
    db_session.commit()


@pytest.fixture(scope="session")
def db_session():
    """Set up and tear down the test database"""
    if not database_exists(SQLALCHEMY_DATABASE_URL):
        create_database(SQLALCHEMY_DATABASE_URL)

    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)
    drop_database(SQLALCHEMY_DATABASE_URL)


@pytest.fixture(scope="session")
def test_app():
    """Create a pytest fixture for the app"""
    client = TestClient(app)
    yield client
