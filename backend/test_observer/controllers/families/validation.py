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

from collections.abc import Iterable, Sequence

from fastapi.exceptions import RequestValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.data_access.models import Family

Loc = tuple[str | int, ...]


def ensure_located_families_exist(db: Session, located: Iterable[tuple[Loc, str]]) -> None:
    """
    Reject family names missing from the family table with a FastAPI-style 422 response.

    Each family is paired with its location in the request, and every unknown one is
    reported at its own location, in request order.
    """
    located = list(located)
    if not located:
        return
    requested = {family for _, family in located}
    known = set(db.scalars(select(Family.name).where(Family.name.in_(requested))))
    errors = [
        {"type": "unknown_family", "loc": loc, "msg": f"Family {family} doesn't exist", "input": family}
        for loc, family in located
        if family not in known
    ]
    if errors:
        raise RequestValidationError(errors)


def ensure_family_exists(db: Session, family: str | None, loc: Loc) -> None:
    """Validate a single, optional family field."""
    if family is not None:
        ensure_located_families_exist(db, [(loc, family)])


def ensure_families_exist(db: Session, families: Sequence[str] | None, loc: Loc) -> None:
    """Validate a list of families, locating each error by its index in the list."""
    ensure_located_families_exist(db, [((*loc, i), family) for i, family in enumerate(families or [])])
