from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from scripts.seed_data import seed_data


def test_seed_data_no_failure(test_client: TestClient, db_session: Session):
    seed_data(test_client, db_session)
