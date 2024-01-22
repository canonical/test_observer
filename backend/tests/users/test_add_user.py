import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from scripts.add_user import add_user
from test_observer.data_access.models import User


def test_create_user(db_session: Session):
    email = "omar.selo@canonical.com"

    user = add_user(email, db_session)

    assert user
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


def test_email_not_in_launchpad():
    email = "john@doe.com"
    with pytest.raises(ValueError, match="Email not registered in launchpad"):
        add_user(email)
