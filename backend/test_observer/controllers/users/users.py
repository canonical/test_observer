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


from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Security, Query
from sqlalchemy import select, func, or_, and_, ColumnElement
from sqlalchemy.orm import Session

from test_observer.common.permissions import Permission, permission_checker
from test_observer.controllers.users.models import (
    UserPatch,
    UserResponse,
    UsersResponse,
)
from test_observer.data_access.models import User
from test_observer.data_access.setup import get_db
from test_observer.users.user_injection import get_current_user


router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserResponse | None)
def get_authenticated_user(user: User | None = Depends(get_current_user)):
    return user


@router.get(
    "",
    response_model=UsersResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_user])],
)
def get_users(
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=1000,
            description="Maximum number of results to return (default: 50)",
        ),
    ] = 50,
    offset: Annotated[
        int,
        Query(
            ge=0,
            description="Number of results to skip for pagination (default: 0)",
        ),
    ] = 0,
    q: Annotated[
        str | None,
        Query(description="Search term for user email, name, launchpad handle, or id"),
    ] = None,
    db: Session = Depends(get_db),
):
    # Build base query with search filter
    query = select(User).order_by(User.name)

    # Build search filters if provided
    search_filters = []
    if q and q.strip():
        # Split search terms on whitespace and filter each one
        search_terms = q.split()
        for term in search_terms:
            search_pattern = f"%{term}%"
            term_filters: list[ColumnElement[bool]] = [
                User.email.ilike(search_pattern),
                User.name.ilike(search_pattern),
                User.launchpad_handle.ilike(search_pattern),
            ]

            # If term is numeric, also search by ID
            if term.isdigit():
                term_filters.append(User.id == int(term))

            search_filters.append(or_(*term_filters))

    # Apply search filters to query
    if search_filters:
        query = query.where(and_(*search_filters))

    # Get total count with same filters
    count_query = select(func.count()).select_from(User)
    if search_filters:
        count_query = count_query.where(and_(*search_filters))
    total_count = db.execute(count_query).scalar() or 0

    # Apply pagination
    query = query.offset(offset).limit(limit)

    # Execute query
    users = db.scalars(query).all()

    return UsersResponse(users=users, count=total_count)  # type: ignore[arg-type]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_user])],
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, f"User with id {user_id} not found")
    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.change_user])],
)
def update_user(
    user_id: int,
    request: UserPatch,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, f"User with id {user_id} not found")

    if request.is_admin is not None:
        user.is_admin = request.is_admin

    db.commit()

    return user
