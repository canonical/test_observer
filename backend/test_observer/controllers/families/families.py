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

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from test_observer.common.permissions import authentication_checker, require_admin
from test_observer.data_access.models import Family
from test_observer.data_access.repository import create_family, get_families
from test_observer.data_access.setup import get_db

from .models import FamilyCreate, FamilyResponse

router = APIRouter(tags=["families"])


@router.get(
    "",
    response_model=list[FamilyResponse],
    dependencies=[Depends(authentication_checker)],
)
def list_families(db: Session = Depends(get_db)) -> list[Family]:
    return get_families(db)


@router.post(
    "",
    status_code=201,
    response_model=FamilyResponse,
    dependencies=[Depends(require_admin)],
    description="Create a family. Only admin users may do this, regardless of IGNORE_PERMISSIONS.",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Administrator access required"},
        409: {"description": "Family already exists"},
    },
)
def add_family(request: FamilyCreate, db: Session = Depends(get_db)) -> Family:
    try:
        return create_family(db, request.name)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Family {request.name} already exists") from error
