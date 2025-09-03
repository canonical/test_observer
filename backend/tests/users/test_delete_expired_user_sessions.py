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


from datetime import datetime, timedelta
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from test_observer.users.delete_expired_user_sessions import (
    delete_expired_user_sessions,
)
from tests.data_generator import DataGenerator


def test_deletes_expired_sesssion(db_session: Session, generator: DataGenerator):
    u = generator.gen_user()
    us = generator.gen_user_session(u, expires_at=datetime.now() - timedelta(hours=1))

    delete_expired_user_sessions(db_session)

    assert inspect(us).deleted


def test_keeps_valid_sesssion(db_session: Session, generator: DataGenerator):
    u = generator.gen_user()
    us = generator.gen_user_session(u, expires_at=datetime.now() + timedelta(hours=1))

    delete_expired_user_sessions(db_session)

    assert not inspect(us).deleted
