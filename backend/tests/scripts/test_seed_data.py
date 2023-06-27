from fastapi.testclient import TestClient

from scripts.seed_data import seed_data


def test_seed_data_no_failure(test_client: TestClient):
    seed_data(test_client)
