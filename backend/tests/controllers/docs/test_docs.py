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

from fastapi.testclient import TestClient

from test_observer.common.permissions import require_authentication
from test_observer.main import app
from tests.data_generator import DataGenerator


def test_openapi_authenticated(test_client: TestClient, generator: DataGenerator):
    application = generator.gen_application(permissions=[])
    response = test_client.get("/openapi.json", headers={"Authorization": f"Bearer {application.api_key}"})
    assert response.status_code == 200
    assert "openapi" in response.json()


def test_openapi_unauthenticated(test_client: TestClient):
    try:
        app.dependency_overrides[require_authentication] = lambda: True
        response = test_client.get("/openapi.json")
        assert response.status_code == 401
    finally:
        app.dependency_overrides.pop(require_authentication, None)


def test_openapi_authentication_disabled(test_client: TestClient):
    try:
        app.dependency_overrides[require_authentication] = lambda: False
        response = test_client.get("/openapi.json")
        assert response.status_code == 200
        assert "openapi" in response.json()
    finally:
        app.dependency_overrides.pop(require_authentication, None)


def test_docs_authenticated(test_client: TestClient, generator: DataGenerator):
    application = generator.gen_application(permissions=[])
    response = test_client.get("/docs", headers={"Authorization": f"Bearer {application.api_key}"})
    assert response.status_code == 200


def test_docs_unauthenticated(test_client: TestClient):
    try:
        app.dependency_overrides[require_authentication] = lambda: True
        response = test_client.get("/docs")
        assert response.status_code == 401
    finally:
        app.dependency_overrides.pop(require_authentication, None)


def test_docs_authentication_disabled(test_client: TestClient):
    try:
        app.dependency_overrides[require_authentication] = lambda: False
        response = test_client.get("/docs")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.pop(require_authentication, None)
