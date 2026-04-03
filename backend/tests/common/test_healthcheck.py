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

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from test_observer.common.healthcheck import create_app
from test_observer.data_access.setup import get_db


@pytest.fixture
def health_client(db_session: Session) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


@pytest.fixture
def health_client_broken_db() -> TestClient:
    broken_db = MagicMock(spec=Session)
    broken_db.execute.side_effect = OperationalError(
        statement="SELECT 1", params={}, orig=Exception("connection refused")
    )

    app = create_app()
    app.dependency_overrides[get_db] = lambda: broken_db
    return TestClient(app, raise_server_exceptions=False)


def test_live_returns_200(health_client: TestClient):
    response = health_client.get("/healthcheck/live")

    assert response.status_code == 200


def test_ready_returns_200_when_db_is_up(health_client: TestClient):
    response = health_client.get("/healthcheck/ready")

    assert response.status_code == 200


def test_ready_returns_500_when_db_is_down(health_client_broken_db: TestClient):
    response = health_client_broken_db.get("/healthcheck/ready")

    assert response.status_code == 500
