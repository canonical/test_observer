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
    assert len(data["api_key"]) == 43

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
