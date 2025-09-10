from fastapi.testclient import TestClient
from tests.data_generator import DataGenerator


def test_get_applications(test_client: TestClient, generator: DataGenerator):
    application = generator.gen_application()

    response = test_client.get("/v1/applications")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": application.id,
            "name": application.name,
            "permissions": application.permissions,
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
    }


def test_update_application_permissions(
    test_client: TestClient, generator: DataGenerator
):
    application = generator.gen_application()

    response = test_client.patch(
        f"/v1/applications/{application.id}",
        json={"permissions": ["update_permission"]},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": application.id,
        "name": application.name,
        "permissions": ["update_permission"],
    }
