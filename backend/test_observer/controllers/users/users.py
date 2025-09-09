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

from test_observer.controllers.users.models import UserPatch, UserResponse
from test_observer.data_access.models import User
from test_observer.data_access.setup import get_db
from test_observer.users.user_injection import get_current_user


router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserResponse | None)
def get_authenticated_user(user: User | None = Depends(get_current_user)):
    return user


@router.get("", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.scalars(select(User))


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, f"User with id {user_id} not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, request: UserPatch, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, f"User with id {user_id} not found")

    if request.is_reviewer is not None:
        user.is_reviewer = request.is_reviewer

    if request.is_admin is not None:
        user.is_admin = request.is_admin

    return user
