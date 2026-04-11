# Copyright 2024 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from test_observer.common.permissions import authentication_checker
from test_observer.controllers.notifications.models import (
    NotificationResponse,
    NotificationsResponse,
)
from test_observer.data_access.models import Notification, User
from test_observer.data_access.setup import get_db
from test_observer.users.user_injection import get_current_user

router = APIRouter(tags=["notifications"])


def _resolve_user_id(
    user_id: str,
    current_user: User | None,
    db: Session,
) -> User:
    """
    Resolve user_id parameter to a User object.
    Supports 'me' as an alias for the current user.
    """
    if user_id == "me":
        if not current_user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return current_user

    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format") from None

    user = db.get(User, user_id_int)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.get(
    "/{id}/notifications",
    response_model=NotificationsResponse,
    dependencies=[Depends(authentication_checker)],
)
@router.get(
    "/{id}/notifications/count",
    response_model=int,
    dependencies=[Depends(authentication_checker)],
)
def get_notifications(
    request: Request,
    id: Annotated[str, Path(description="User ID or 'me' for current user")],
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
    unread_only: Annotated[
        bool,
        Query(
            description="Whether to return only unread notifications (default: false)",
        ),
    ] = False,
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all notifications for the specified user"""

    # Notifications only make sense in the context of a user
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    target_user = _resolve_user_id(id, user, db)

    # Get total count
    count_query = select(func.count(Notification.id)).where(Notification.user_id == target_user.id)
    if unread_only:
        count_query = count_query.where(Notification.dismissed_at.is_(None))
    total_count = db.scalar(count_query) or 0

    if request.url.path.endswith("/count"):
        return total_count

    # Get paginated notifications
    select_query = select(Notification).where(Notification.user_id == target_user.id)
    if unread_only:
        select_query = select_query.where(Notification.dismissed_at.is_(None))
    notifications = db.scalars(select_query.order_by(Notification.created_at.desc()).limit(limit).offset(offset)).all()

    return NotificationsResponse(
        notifications=list(notifications),  # type: ignore[arg-type]
        count=total_count,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/{id}/notifications/{notification_id}/dismiss",
    response_model=NotificationResponse,
    dependencies=[Depends(authentication_checker)],
)
def mark_notification_as_read(
    id: Annotated[str, Path(description="User ID or 'me' for current user")],
    notification_id: int,
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a notification as read"""
    # Notifications only make sense in the context of a user
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    target_user = _resolve_user_id(id, user, db)

    notification = db.scalar(
        select(Notification).where(Notification.id == notification_id).where(Notification.user_id == target_user.id)
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if notification.dismissed_at is None:
        notification.dismissed_at = datetime.now()
        db.commit()
        db.refresh(notification)

    return notification
