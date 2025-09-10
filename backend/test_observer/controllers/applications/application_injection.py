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

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_observer.data_access.models import Application
from test_observer.data_access.setup import get_db


def get_current_application(
    request: Request, db: Session = Depends(get_db)
) -> Application | None:
    match request.headers.get("Authorization", "").split():
        case ["Bearer", token]:
            return db.scalar(select(Application).where(Application.api_key == token))
        case _:
            return None
