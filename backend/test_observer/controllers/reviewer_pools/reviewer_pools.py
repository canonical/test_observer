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


from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from test_observer.common.permissions import Permission, permission_checker
from test_observer.data_access.models import ReviewerPool, User
from test_observer.data_access.setup import get_db
from test_observer.users.user_injection import get_current_user

from .models import ReviewerPoolResponse


router = APIRouter(tags=["reviewer-pools"])


@router.get(
    "",
    response_model=list[ReviewerPoolResponse],
    dependencies=[Security(permission_checker, scopes=[Permission.view_user])],
)
def get_reviewer_pools(
    db: Session = Depends(get_db),
):
    """Get all reviewer pools with their members"""
    pools = db.scalars(
        select(ReviewerPool).options(selectinload(ReviewerPool.members))
    ).all()
    return pools


@router.get(
    "/{pool_id}",
    response_model=ReviewerPoolResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_user])],
)
def get_reviewer_pool(
    pool_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific reviewer pool with its members"""
    pool = db.get(ReviewerPool, pool_id, options=[selectinload(ReviewerPool.members)])
    if pool is None:
        raise HTTPException(404, f"Reviewer pool with id {pool_id} not found")
    return pool


@router.post(
    "/{pool_id}/members/{user_id}",
    response_model=ReviewerPoolResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.change_user])],
)
def add_member_to_pool(
    pool_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    """Add a user to a reviewer pool (admin only)"""
    if not current_user or not current_user.is_admin:
        raise HTTPException(403, "Only admins can manage reviewer pools")

    pool = db.get(ReviewerPool, pool_id, options=[selectinload(ReviewerPool.members)])
    if pool is None:
        raise HTTPException(404, f"Reviewer pool with id {pool_id} not found")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, f"User with id {user_id} not found")

    if user not in pool.members:
        pool.members.append(user)
        db.commit()

    return pool


@router.delete(
    "/{pool_id}/members/{user_id}",
    response_model=ReviewerPoolResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.change_user])],
)
def remove_member_from_pool(
    pool_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    """Remove a user from a reviewer pool (admin only)"""
    if not current_user or not current_user.is_admin:
        raise HTTPException(403, "Only admins can manage reviewer pools")

    pool = db.get(ReviewerPool, pool_id, options=[selectinload(ReviewerPool.members)])
    if pool is None:
        raise HTTPException(404, f"Reviewer pool with id {pool_id} not found")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, f"User with id {user_id} not found")

    if user in pool.members:
        pool.members.remove(user)
        db.commit()

    return pool
