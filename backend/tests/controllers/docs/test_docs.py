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

from test_observer.common.enums import Permission
from tests.conftest import make_authenticated_request


def test_openapi_with_permission(test_client: TestClient):
    response = make_authenticated_request(
        lambda: test_client.get("/openapi.json"),
        Permission.view_docs,
    )
    assert response.status_code == 200
    assert "openapi" in response.json()


def test_openapi_without_permission(test_client: TestClient):
    response = make_authenticated_request(
        lambda: test_client.get("/openapi.json"),
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions"}


def test_docs_with_permission(test_client: TestClient):
    response = make_authenticated_request(
        lambda: test_client.get("/docs"),
        Permission.view_docs,
    )
    assert response.status_code == 200


def test_docs_without_permission(test_client: TestClient):
    response = make_authenticated_request(
        lambda: test_client.get("/docs"),
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions"}
