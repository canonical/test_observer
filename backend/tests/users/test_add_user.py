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


import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from scripts.add_user import add_user
from test_observer.data_access.models import User
from tests.fake_launchpad_api import FakeLaunchpadAPI


def test_create_user(db_session: Session):
    email = "john.doe@canonical.com"

    user = add_user(email, db_session, FakeLaunchpadAPI())

    assert user
    assert (
        db_session.execute(
            select(User).where(
                User.launchpad_email == email,
                User.launchpad_handle == "john-doe",
                User.name == "John Doe",
            )
        ).scalar_one_or_none()
        is not None
    )


def test_email_not_in_launchpad():
    email = "missing-email@canonical.com"
    with pytest.raises(ValueError, match="Email not registered in launchpad"):
        add_user(email, launchpad_api=FakeLaunchpadAPI())
