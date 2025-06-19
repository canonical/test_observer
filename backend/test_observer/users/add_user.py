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


from sqlalchemy.orm import Session
from sqlalchemy import select

from test_observer.data_access.models import User
from test_observer.data_access.setup import SessionLocal
from test_observer.external_apis.launchpad.launchpad_api import LaunchpadAPI
from test_observer.external_apis.launchpad.models import LaunchpadUser


def add_user(
    launchpad_email: str,
    session: Session | None = None,
    launchpad_api: LaunchpadAPI | None = None,
):
    if not launchpad_api:
        launchpad_api = LaunchpadAPI()

    launchpad_user = launchpad_api.get_user_by_email(launchpad_email)
    if not launchpad_user:
        raise ValueError("Email not registered in launchpad")

    if session is None:
        session = SessionLocal()
        try:
            return _create_user(launchpad_user, session)
        finally:
            session.close()
    else:
        return _create_user(launchpad_user, session)


def _create_user(launchpad_user: LaunchpadUser, session: Session) -> User:
    # Check if user already exists
    existing_user = session.scalar(
        select(User).where(User.launchpad_email == launchpad_user.email)
    )
    if existing_user:
        print(f"User with email {launchpad_user.email} already exists. Skipping creation.")
        return existing_user
    
    user = User(
        launchpad_handle=launchpad_user.handle,
        launchpad_email=launchpad_user.email,
        name=launchpad_user.name,
    )
    session.add(user)
    session.commit()
    return user
