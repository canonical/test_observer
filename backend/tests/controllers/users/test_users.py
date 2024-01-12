from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.data_access.models import User


def test_create_user(db_session: Session, test_client: TestClient):
    email = "omar.selo@canonical.com"
    response = test_client.post("/v1/users", json={"launchpad_email": email})

    assert response.status_code == 200
    assert (
        db_session.execute(
            select(User).where(
                User.launchpad_email == email,
                User.launchpad_handle == "omar-selo",
                User.name == "Omar Abou Selo",
            )
        ).scalar_one_or_none()
        is not None
    )


def test_email_not_in_launchpad(test_client: TestClient):
    email = "john@doe.com"
    response = test_client.post("/v1/users", json={"launchpad_email": email})

    assert response.status_code == 422
    assert response.json()["detail"] == "Email not registered in launchpad"
