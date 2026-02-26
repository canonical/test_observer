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

import logging

from sqlalchemy.orm import Session
from sqlalchemy import select

from test_observer.data_access.models import User
from test_observer.data_access.setup import SessionLocal

logger = logging.getLogger("test-observer-backend")


def promote_user_to_admin(
    email: str,
    session: Session | None = None,
):
    if session is None:
        session = SessionLocal()
        try:
            return _promote_user(email, session)
        finally:
            session.close()
    else:
        return _promote_user(email, session)


def _promote_user(email: str, session: Session) -> User:
    user = session.scalar(select(User).where(User.email == email))
    if not user:
        raise ValueError(f"User with email {email} not found")

    if user.is_admin:
        logger.info(
            "User with email %s is already admin. Skipping promotion.",
            email,
        )
        return user

    user.is_admin = True
    session.commit()

    logger.info(
        "User with email %s promoted to admin successfully.",
        email,
    )
    return user
