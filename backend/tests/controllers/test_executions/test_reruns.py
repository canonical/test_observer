from fastapi.testclient import TestClient

from tests.data_generator import DataGenerator

reruns_url = "/v1/test-executions/reruns"


def test_post_no_data_returns_422(test_client: TestClient):
    response = test_client.post(reruns_url)
    assert response.status_code == 422


def test_post_invalid_id_returns_404_with_message(test_client: TestClient):
    response = test_client.post(reruns_url, json={"test_execution_id": 1})
    assert response.status_code == 404
    assert response.json()["detail"] == "No test execution with id 1 found"


def test_valid_post_returns_200(test_client: TestClient, generator: DataGenerator):
    a = generator.gen_artefact("beta")
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment()
    te = generator.gen_test_execution(ab, e)

    response = test_client.post(reruns_url, json={"test_execution_id": te.id})
    assert response.status_code == 200


def test_get_returns_200_with_empty_list(test_client: TestClient):
    response = test_client.get(reruns_url)
    assert response.status_code == 200
    assert response.json() == []
