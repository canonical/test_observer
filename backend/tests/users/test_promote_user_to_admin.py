# Copyright 2025 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.data_access.models import User
from test_observer.users.promote_user_to_admin import promote_user_to_admin


def test_promote_user_to_admin(db_session: Session):
    email = "john.doe@canonical.com"
    user = User(
        launchpad_handle="john-doe",
        email=email,
        name="John Doe",
        is_admin=False,
    )
    db_session.add(user)
    db_session.commit()

    promoted_user = promote_user_to_admin(email, db_session)

    assert promoted_user
    assert promoted_user.is_admin is True

    db_user = db_session.scalar(select(User).where(User.email == email))
    assert db_user is not None
    assert db_user.is_admin is True


def test_promote_user_already_admin(db_session: Session):
    email = "admin@canonical.com"

    user = User(
        launchpad_handle="admin-user",
        email=email,
        name="Admin User",
        is_admin=True,
    )
    db_session.add(user)
    db_session.commit()

    promoted_user = promote_user_to_admin(email, db_session)

    assert promoted_user
    assert promoted_user.is_admin is True


def test_promote_user_not_found(db_session: Session):
    email = "nonexistent@canonical.com"

    with pytest.raises(ValueError, match="User with email nonexistent@canonical.com not found"):
        promote_user_to_admin(email, db_session)
