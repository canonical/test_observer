# Copyright 2026 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from collections.abc import Iterable

from fastapi.exceptions import RequestValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.data_access.models import Family


def ensure_families_exist(db: Session, families: Iterable[str] | None, loc: tuple[str, ...]) -> None:
    """Reject family names missing from the family table with FastAPI's standard 422 response."""
    requested = set(families or ())
    if not requested:
        return
    known = set(db.scalars(select(Family.name).where(Family.name.in_(requested))))
    unknown = sorted(requested - known)
    if unknown:
        raise RequestValidationError(
            [
                {"type": "unknown_family", "loc": loc, "msg": f"Family {name} doesn't exist", "input": name}
                for name in unknown
            ]
        )
