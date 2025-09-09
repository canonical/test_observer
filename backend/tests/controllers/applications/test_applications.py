from fastapi.testclient import TestClient
from tests.data_generator import DataGenerator


def test_get_applications(test_client: TestClient, generator: DataGenerator):
    team = generator.gen_team()
    application = generator.gen_application(teams=[team])

    response = test_client.get("/v1/applications")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": application.id,
            "name": application.name,
            "teams": [
                {
                    "id": team.id,
                    "name": team.name,
                    "permissions": team.permissions,
                }
            ],
        }
    ]


def test_get_application(test_client: TestClient, generator: DataGenerator):
    team = generator.gen_team()
    application = generator.gen_application(teams=[team])

    response = test_client.get(f"/v1/applications/{application.id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": application.id,
        "name": application.name,
        "teams": [
            {
                "id": team.id,
                "name": team.name,
                "permissions": team.permissions,
            }
        ],
    }
