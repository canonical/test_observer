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

import json
from base64 import b64encode
from datetime import datetime

import itsdangerous
from fastapi.testclient import TestClient

from test_observer.common.config import SESSIONS_SECRET
from test_observer.data_access.models import User
from test_observer.data_access.models_enums import NotificationType
from tests.data_generator import DataGenerator


def _create_session_cookie(session_id: int) -> str:
    """Create a signed session cookie for testing"""
    signer = itsdangerous.TimestampSigner(str(SESSIONS_SECRET))
    session_data = {"id": session_id}
    session_json = json.dumps(session_data)
    return signer.sign(b64encode(session_json.encode()).decode()).decode()


def _authenticate_user(test_client: TestClient, user: User, generator: DataGenerator) -> None:
    """Helper to authenticate a user in test client"""
    session = generator.gen_user_session(user)
    session_cookie = _create_session_cookie(session.id)
    test_client.cookies.set("session", session_cookie)


def test_get_notifications_without_auth(test_client: TestClient):
    """Test that accessing notifications without auth returns 401"""
    response = test_client.get("/v1/notifications")
    assert response.status_code == 401


def test_get_notifications(test_client: TestClient, generator: DataGenerator):
    """Test getting all notifications for a user"""
    user = generator.gen_user(email="notifications@test.com")
    notification1 = generator.gen_notification(
        user=user,
        notification_type=NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW,
        target_url="/artefacts/1",
    )
    notification2 = generator.gen_notification(
        user=user,
        notification_type=NotificationType.USER_ASSIGNED_ENVIRONMENT_REVIEW,
        target_url="/artefacts/2",
        dismissed_at=datetime.now(),
    )

    # Another user's notification (should not appear)
    other_user = generator.gen_user(email="other@test.com")
    generator.gen_notification(user=other_user)

    _authenticate_user(test_client, user, generator)
    response = test_client.get("/v1/notifications", headers={"X-CSRF-Token": "1"})

    assert response.status_code == 200
    data = response.json()
    assert len(data["notifications"]) == 2
    assert data["notifications"][0]["id"] in [notification1.id, notification2.id]
    assert data["notifications"][1]["id"] in [notification1.id, notification2.id]
    assert data["count"] == 2
    assert data["limit"] == 50
    assert data["offset"] == 0


def test_get_unread_count_without_auth(test_client: TestClient):
    """Test that accessing unread count without auth returns 401"""
    response = test_client.get("/v1/notifications/unread-count")
    assert response.status_code == 401


def test_get_unread_count(test_client: TestClient, generator: DataGenerator):
    """Test getting unread notification count"""
    user = generator.gen_user(email="unread@test.com")
    generator.gen_notification(user=user)
    generator.gen_notification(user=user)
    generator.gen_notification(user=user, dismissed_at=datetime.now())

    # Another user's notification (should not be counted)
    other_user = generator.gen_user(email="other-unread@test.com")
    generator.gen_notification(user=other_user)

    _authenticate_user(test_client, user, generator)
    response = test_client.get("/v1/notifications/unread-count", headers={"X-CSRF-Token": "1"})

    assert response.status_code == 200
    assert response.json() == 2


def test_mark_notification_as_read_without_auth(test_client: TestClient, generator: DataGenerator):
    """Test that marking notification as read without auth returns 401"""
    user = generator.gen_user(email="mark-no-auth@test.com")
    notification = generator.gen_notification(user=user)

    response = test_client.patch(f"/v1/notifications/{notification.id}/read")
    assert response.status_code == 401


def test_mark_notification_as_read(test_client: TestClient, generator: DataGenerator):
    """Test marking a notification as read"""
    user = generator.gen_user(email="mark-read@test.com")
    notification = generator.gen_notification(user=user)

    assert notification.dismissed_at is None

    _authenticate_user(test_client, user, generator)
    response = test_client.patch(f"/v1/notifications/{notification.id}/read", headers={"X-CSRF-Token": "1"})

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == notification.id
    assert data["dismissed_at"] is not None


def test_mark_notification_as_read_wrong_user(test_client: TestClient, generator: DataGenerator):
    """Test that a user cannot mark another user's notification as read"""
    user = generator.gen_user(email="wrong-user@test.com")
    other_user = generator.gen_user(email="wrong-user-other@test.com")
    notification = generator.gen_notification(user=user)

    _authenticate_user(test_client, other_user, generator)
    response = test_client.patch(f"/v1/notifications/{notification.id}/read", headers={"X-CSRF-Token": "1"})

    assert response.status_code == 404


def test_mark_nonexistent_notification_as_read(test_client: TestClient, generator: DataGenerator):
    """Test marking a non-existent notification as read returns 404"""
    user = generator.gen_user(email="nonexistent@test.com")

    _authenticate_user(test_client, user, generator)
    response = test_client.patch("/v1/notifications/99999/read", headers={"X-CSRF-Token": "1"})

    assert response.status_code == 404


def test_get_notifications_with_pagination(test_client: TestClient, generator: DataGenerator):
    """Test getting notifications with limit and offset"""
    user = generator.gen_user(email="pagination@test.com")

    # Create 5 notifications
    notifications = []
    for i in range(5):
        notification = generator.gen_notification(
            user=user,
            notification_type=NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW,
            target_url=f"/artefacts/{i}",
        )
        notifications.append(notification)

    _authenticate_user(test_client, user, generator)

    # Test limit
    response = test_client.get("/v1/notifications?limit=2", headers={"X-CSRF-Token": "1"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["notifications"]) == 2
    assert data["count"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 0

    # Test offset
    response = test_client.get("/v1/notifications?limit=2&offset=2", headers={"X-CSRF-Token": "1"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["notifications"]) == 2
    assert data["count"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 2

    # Test offset beyond results
    response = test_client.get("/v1/notifications?limit=10&offset=3", headers={"X-CSRF-Token": "1"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["notifications"]) == 2
    assert data["count"] == 5
    assert data["limit"] == 10
    assert data["offset"] == 3
