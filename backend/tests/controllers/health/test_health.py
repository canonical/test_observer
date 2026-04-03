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

from collections.abc import Callable
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from test_observer.data_access.setup import get_db
from test_observer.main import app


@pytest.fixture
def make_client():
    initial_get_db_override = app.dependency_overrides.pop(get_db, None)

    def _make_client(local: bool, db_broken: bool) -> TestClient:
        if db_broken:
            broken_db = MagicMock(spec=Session)
            broken_db.execute.side_effect = OperationalError(
                statement="SELECT 1", params={}, orig=Exception("connection refused")
            )
            app.dependency_overrides[get_db] = lambda: broken_db

        client = ("127.0.0.1", 12345) if local else ("123.45.67.89", 12345)
        return TestClient(app, client=client)

    yield _make_client

    # We always clear any dependency override that could be set by the test
    app.dependency_overrides.pop(get_db, None)
    # Then we restore the initial override if there was one
    if initial_get_db_override is not None:
        app.dependency_overrides[get_db] = initial_get_db_override


def test_live_returns_200(make_client: Callable[[bool, bool], TestClient]):
    response = make_client(True, False).get("/health/live")
    assert response.status_code == 200


def test_live_returns_403_for_remote_client(make_client: Callable[[bool, bool], TestClient]):
    response = make_client(False, False).get("/health/live")
    assert response.status_code == 403


def test_ready_returns_200_when_db_is_up(make_client: Callable[[bool, bool], TestClient]):
    response = make_client(True, False).get("/health/ready")
    assert response.status_code == 200


def test_ready_returns_403_for_remote_client(make_client: Callable[[bool, bool], TestClient]):
    response = make_client(False, False).get("/health/ready")
    assert response.status_code == 403


def test_ready_returns_503_when_db_is_down(make_client: Callable[[bool, bool], TestClient]):
    response = make_client(True, True).get("/health/ready")
    assert response.status_code == 503
