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

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.controllers.applications.models import (
    ApplicationPatch,
    ApplicationResponse,
)
from test_observer.data_access.models import Application
from test_observer.data_access.setup import get_db


router: APIRouter = APIRouter(tags=["applications"])


@router.get("", response_model=list[ApplicationResponse])
def get_users(db: Session = Depends(get_db)):
    return db.scalars(select(Application))


@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(application_id: int, db: Session = Depends(get_db)):
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(404, f"Application with id {application_id} not found")
    return application


@router.patch("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: int, request: ApplicationPatch, db: Session = Depends(get_db)
):
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(404, f"Application {application_id} doesn't exist")

    if request.permissions:
        application.permissions = [p.value for p in request.permissions]
        db.commit()

    return application
