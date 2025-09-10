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

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from test_observer.common.permissions import Permission
from test_observer.data_access.models import Application
from tests.data_generator import DataGenerator


def test_create_application(test_client: TestClient, db_session: Session):
    response = test_client.post(
        "/v1/applications",
        json={"name": "myscript", "permissions": [Permission.update_permission]},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "myscript"
    assert data["permissions"] == [Permission.update_permission]
    assert "api_key" in data
    assert len(data["api_key"]) == 46
    assert data["api_key"][0:3] == "to_"

    app_id = data["id"]
    app = db_session.get(Application, app_id)
    assert app is not None
    assert app.name == "myscript"
    assert app.permissions == [Permission.update_permission]
    assert app.api_key == data["api_key"]


def test_get_applications(test_client: TestClient, generator: DataGenerator):
    application = generator.gen_application()

    response = test_client.get("/v1/applications")

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

    response = test_client.get(f"/v1/applications/{application.id}")

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

    response = test_client.patch(
        f"/v1/applications/{application.id}",
        json={"permissions": [Permission.update_permission]},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": application.id,
        "name": application.name,
        "permissions": [Permission.update_permission],
        "api_key": application.api_key,
    }
