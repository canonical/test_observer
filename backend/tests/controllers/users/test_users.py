from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.data_access.models import User


def test_create_user(db_session: Session, test_client: TestClient):
    handle = "someuser"
    response = test_client.post("/v1/users/", json={"launchpad_handle": handle})

    assert response.status_code == 200
    assert response.json()["launchpad_handle"] == handle
    assert (
        db_session.execute(
            select(User).where(User.launchpad_handle == handle)
        ).scalar_one_or_none()
        is not None
    )
