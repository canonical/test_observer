# Copyright 2025 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from test_observer.common.permissions import Permission
from test_observer.data_access.models import Application
from tests.conftest import make_authenticated_request
from tests.data_generator import DataGenerator


def test_create_application(test_client: TestClient, db_session: Session):
    response = make_authenticated_request(
        lambda: test_client.post(
            "/v1/applications",
            json={"name": "myscript", "permissions": [Permission.view_user]},
        ),
        Permission.add_application,
    )

    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "myscript"
    assert data["permissions"] == [Permission.view_user]
    assert "api_key" in data
    # Taking into consideration base64 encoded 32 bytes of entropy
    # together with "to_" prefix results in exactly 46 characters
    assert len(data["api_key"]) == 46
    # prefix to_ is to indicate that this is an api key for Test Observer (TO)
    assert data["api_key"][0:3] == "to_"

    app_id = data["id"]
    app = db_session.get(Application, app_id)
    assert app is not None
    assert app.name == "myscript"
    assert app.permissions == [Permission.view_user]
    assert app.api_key == data["api_key"]


def test_get_applications(test_client: TestClient, generator: DataGenerator):
    application = generator.gen_application()

    response = make_authenticated_request(
        lambda: test_client.get("/v1/applications"), Permission.view_application
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": application.id,
            "name": application.name,
            "permissions": application.permissions,
            "api_key": application.api_key,
        }
    ]


def test_get_application(test_client: TestClient, generator: DataGenerator):
    application = generator.gen_application()

    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/applications/{application.id}"),
        Permission.view_application,
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": application.id,
        "name": application.name,
        "permissions": application.permissions,
        "api_key": application.api_key,
    }


def test_get_current_application(test_client: TestClient, generator: DataGenerator):
    application = generator.gen_application()

    response = test_client.get(
        "/v1/applications/me",
        headers={"Authorization": f"Bearer {application.api_key}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": application.id,
        "name": application.name,
        "permissions": application.permissions,
        "api_key": application.api_key,
    }


def test_update_application_permissions(
    test_client: TestClient, generator: DataGenerator
):
    application = generator.gen_application()

    response = make_authenticated_request(
        lambda: test_client.patch(
            f"/v1/applications/{application.id}",
            json={"permissions": [Permission.view_user]},
        ),
        Permission.change_application,
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": application.id,
        "name": application.name,
        "permissions": [Permission.view_user],
        "api_key": application.api_key,
    }
