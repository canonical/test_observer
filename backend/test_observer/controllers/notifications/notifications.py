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

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from test_observer.controllers.notifications.models import (
    NotificationResponse,
    NotificationsResponse,
)
from test_observer.data_access.models import Notification, User
from test_observer.data_access.setup import get_db
from test_observer.users.user_injection import get_current_user

router = APIRouter(tags=["notifications"])


@router.get("", response_model=NotificationsResponse)
def get_notifications(
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all notifications for the logged in user"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    notifications = db.scalars(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
    ).all()

    return NotificationsResponse(notifications=list(notifications))


@router.get("/unread-count", response_model=int)
def get_unread_count(
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the count of unread notifications for the logged in user"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    count = db.scalar(
        select(func.count(Notification.id))
        .where(Notification.user_id == user.id)
        .where(Notification.dismissed_at.is_(None))
    )

    return count or 0


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
    notification_id: int,
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a notification as read"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    notification = db.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if notification.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this notification")

    notification.dismissed_at = datetime.now()
    db.commit()
    db.refresh(notification)

    return notification
