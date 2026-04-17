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

from collections.abc import Sequence
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Security
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from test_observer.common.enums import Permission
from test_observer.common.permissions import permission_checker, requires_authentication
from test_observer.controllers.applications.application_injection import get_current_application
from test_observer.controllers.notifications.models import (
    NotificationResponse,
    NotificationsResponse,
)
from test_observer.data_access.models import Application, Notification, User
from test_observer.data_access.setup import get_db
from test_observer.users.user_injection import get_current_user

router = APIRouter(tags=["notifications"])


def _get_user_notification_count(db: Session, user_id: int, unread_only: bool) -> int:
    query = select(func.count(Notification.id)).where(Notification.user_id == user_id)
    if unread_only:
        query = query.where(Notification.dismissed_at.is_(None))
    # The or 0 is just to satisfy the type checker
    return db.scalar(query) or 0


def _get_user_notifications(
    db: Session, user_id: int, limit: int, offset: int, unread_only: bool
) -> Sequence[Notification]:
    query = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        query = query.where(Notification.dismissed_at.is_(None))
    return db.scalars(query.order_by(Notification.created_at.desc()).limit(limit).offset(offset)).all()


@router.get("/me/notifications", response_model=NotificationsResponse)
def get_own_notifications(
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
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
    application: Application | None = Depends(get_current_application),
    authentication_required: bool = Depends(requires_authentication),
):
    """Get all notifications for the authenticated user"""
    # Even if an app is authenticated, it doesn't make sense for an app to access this endpoint,
    # since notifications are inherently user-specific. Thus, we require a user.
    if authentication_required and user is None and application is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if authentication_required and user is None and application is not None:
        raise HTTPException(status_code=403, detail="Forbidden")

    # If authentication is not required, we might not have a user
    if user is None:
        return NotificationsResponse(notifications=[], count=0, limit=limit, offset=offset)

    count = _get_user_notification_count(db, user.id, unread_only)
    notifications = _get_user_notifications(db, user.id, limit, offset, unread_only)
    return NotificationsResponse(
        notifications=notifications,  # type: ignore[arg-type]
        count=count,
        limit=limit,
        offset=offset,
    )


@router.get("/me/notifications/count", response_model=int)
def get_own_notification_count(
    unread_only: Annotated[
        bool,
        Query(
            description="Whether to return only unread notifications (default: false)",
        ),
    ] = False,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
    application: Application | None = Depends(get_current_application),
    authentication_required: bool = Depends(requires_authentication),
):
    """Get the count of notifications for the authenticated user"""
    # Even if an app is authenticated, it doesn't make sense for an app to access this endpoint,
    # since notifications are inherently user-specific. Thus, we require a user.
    if authentication_required and user is None and application is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if authentication_required and user is None and application is not None:
        raise HTTPException(status_code=403, detail="Forbidden")

    # If authentication is not required, we might not have a user
    if user is None:
        return 0

    return _get_user_notification_count(db, user.id, unread_only)


@router.post(
    "/me/notifications/{notification_id}/dismiss",
    response_model=NotificationResponse,
)
def mark_own_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
    application: Application | None = Depends(get_current_application),
):
    """Mark the authenticated user's own notification as read"""

    # In this case, regardless of whether authentication is required,
    # this endpoint only makes sense if a user is authenticated
    if user is None:
        if application is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        else:
            raise HTTPException(status_code=403, detail="Forbidden")

    notification = db.scalar(
        select(Notification).where(Notification.id == notification_id).where(Notification.user_id == user.id)
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if notification.dismissed_at is None:
        notification.dismissed_at = datetime.now()
        db.commit()
        db.refresh(notification)

    return notification


@router.get(
    "/{user_id}/notifications",
    response_model=NotificationsResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_notification])],
)
def get_notifications(
    user_id: Annotated[int, Path(description="ID of the user whose notifications will be fetched")],
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
    db: Session = Depends(get_db),
):
    """Get all notifications for the specified user"""

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    count = _get_user_notification_count(db, user_id, unread_only)
    notifications = _get_user_notifications(db, user_id, limit, offset, unread_only)
    return NotificationsResponse(
        notifications=list(notifications),  # type: ignore[arg-type]
        count=count,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{user_id}/notifications/count",
    response_model=int,
    dependencies=[Security(permission_checker, scopes=[Permission.view_notification])],
)
def get_notification_count(
    user_id: Annotated[int, Path(description="ID of the user whose notification count will be fetched")],
    unread_only: Annotated[
        bool,
        Query(
            description="Whether to return only unread notifications (default: false)",
        ),
    ] = False,
    db: Session = Depends(get_db),
):
    """Get the count of notifications for the specified user"""

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return _get_user_notification_count(db, user_id, unread_only)


@router.post(
    "/{user_id}/notifications/{notification_id}/dismiss",
    response_model=NotificationResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.change_notification])],
)
def mark_notification_as_read(
    user_id: Annotated[int, Path(description="ID of the user whose notification will be dismissed")],
    notification_id: int,
    db: Session = Depends(get_db),
):
    """Mark a notification as read"""

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    notification = db.scalar(
        select(Notification).where(Notification.id == notification_id).where(Notification.user_id == user_id)
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if notification.dismissed_at is None:
        notification.dismissed_at = datetime.now()
        db.commit()
        db.refresh(notification)

    return notification
