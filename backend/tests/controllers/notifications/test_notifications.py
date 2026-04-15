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

from collections.abc import Callable
from datetime import datetime

from fastapi.testclient import TestClient

from test_observer.common.enums import Permission
from test_observer.common.permissions import requires_authentication
from test_observer.data_access.models import Notification
from test_observer.data_access.models_enums import NotificationType
from test_observer.main import app
from tests.conftest import authenticate_user, make_authenticated_request
from tests.data_generator import DataGenerator


def test_get_own_notifications_unauthenticated_auth_not_required(test_client: TestClient):
    try:
        app.dependency_overrides[requires_authentication] = lambda: False
        response = test_client.get("/v1/users/me/notifications")
        assert response.status_code == 200
        assert response.json() == {"notifications": [], "count": 0, "limit": 50, "offset": 0}
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_get_own_notifications_count_unauthenticated_auth_not_required(test_client: TestClient):
    try:
        app.dependency_overrides[requires_authentication] = lambda: False
        response = test_client.get("/v1/users/me/notifications/count")
        assert response.status_code == 200
        assert response.json() == 0
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_get_own_notifications_unauthenticated_auth_required(test_client: TestClient):
    try:
        app.dependency_overrides[requires_authentication] = lambda: True
        response = test_client.get("/v1/users/me/notifications")
        assert response.status_code == 401
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_get_own_notifications_count_unauthenticated_auth_required(test_client: TestClient):
    try:
        app.dependency_overrides[requires_authentication] = lambda: True
        response = test_client.get("/v1/users/me/notifications/count")
        assert response.status_code == 401
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_get_own_notifications_authenticated_user_auth_not_required(
    test_client: TestClient, generator: DataGenerator, create_session_cookie: Callable[[int], str]
):
    try:
        app.dependency_overrides[requires_authentication] = lambda: False
        user = generator.gen_user(email="user@test.com")
        notification = generator.gen_notification(user=user)
        authenticate_user(test_client, user, generator, create_session_cookie)
        response = test_client.get("/v1/users/me/notifications", headers={"X-CSRF-Token": "1"})
        assert response.status_code == 200
        json_ = response.json()
        assert json_.get("count") == 1
        assert len(json_.get("notifications", [])) == 1
        assert json_["notifications"][0]["id"] == notification.id
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_get_own_notifications_count_authenticated_user_auth_not_required(
    test_client: TestClient, generator: DataGenerator, create_session_cookie: Callable[[int], str]
):
    try:
        app.dependency_overrides[requires_authentication] = lambda: False
        user = generator.gen_user(email="user@test.com")
        generator.gen_notification(user=user)
        authenticate_user(test_client, user, generator, create_session_cookie)
        response = test_client.get("/v1/users/me/notifications/count", headers={"X-CSRF-Token": "1"})
        assert response.status_code == 200
        assert response.json() == 1
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_get_own_notifications_authenticated_user_auth_required(
    test_client: TestClient, generator: DataGenerator, create_session_cookie: Callable[[int], str]
):
    try:
        app.dependency_overrides[requires_authentication] = lambda: True
        user = generator.gen_user(email="user@test.com")
        notification = generator.gen_notification(user=user)
        authenticate_user(test_client, user, generator, create_session_cookie)
        response = test_client.get("/v1/users/me/notifications", headers={"X-CSRF-Token": "1"})
        assert response.status_code == 200
        json_ = response.json()
        assert json_.get("count") == 1
        assert len(json_.get("notifications", [])) == 1
        assert json_["notifications"][0]["id"] == notification.id
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_get_own_notifications_count_authenticated_user_auth_required(
    test_client: TestClient, generator: DataGenerator, create_session_cookie: Callable[[int], str]
):
    try:
        app.dependency_overrides[requires_authentication] = lambda: True
        user = generator.gen_user(email="user@test.com")
        generator.gen_notification(user=user)
        authenticate_user(test_client, user, generator, create_session_cookie)
        response = test_client.get("/v1/users/me/notifications/count", headers={"X-CSRF-Token": "1"})
        assert response.status_code == 200
        assert response.json() == 1
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_get_own_notifications_authenticated_app_auth_not_required(test_client: TestClient, generator: DataGenerator):
    try:
        app.dependency_overrides[requires_authentication] = lambda: False
        application = generator.gen_application(permissions=[])
        response = test_client.get(
            "/v1/users/me/notifications", headers={"Authorization": f"Bearer {application.api_key}"}
        )
        assert response.status_code == 200
        assert response.json() == {"notifications": [], "count": 0, "limit": 50, "offset": 0}
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_get_own_notifications_count_authenticated_app_auth_not_required(
    test_client: TestClient, generator: DataGenerator
):
    try:
        app.dependency_overrides[requires_authentication] = lambda: False
        application = generator.gen_application(permissions=[])
        response = test_client.get(
            "/v1/users/me/notifications/count", headers={"Authorization": f"Bearer {application.api_key}"}
        )
        assert response.status_code == 200
        assert response.json() == 0
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_get_own_notifications_authenticated_app_auth_required(test_client: TestClient, generator: DataGenerator):
    try:
        app.dependency_overrides[requires_authentication] = lambda: True
        application = generator.gen_application(permissions=[])
        response = test_client.get(
            "/v1/users/me/notifications", headers={"Authorization": f"Bearer {application.api_key}"}
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_get_own_notifications_count_authenticated_app_auth_required(test_client: TestClient, generator: DataGenerator):
    try:
        app.dependency_overrides[requires_authentication] = lambda: True
        application = generator.gen_application(permissions=[])
        response = test_client.get(
            "/v1/users/me/notifications/count", headers={"Authorization": f"Bearer {application.api_key}"}
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(requires_authentication, None)


def test_get_notifications_user_no_permissions(
    test_client: TestClient, generator: DataGenerator, create_session_cookie: Callable[[int], str]
):
    """Test that a user without view_notification permission cannot get notifications"""
    user = generator.gen_user(email="no-permissions@test.com")
    authenticate_user(test_client, user, generator, create_session_cookie)
    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/users/{user.id}/notifications", headers={"X-CSRF-Token": "1"}),
    )
    assert response.status_code == 403


def test_get_notifications_app_no_permissions(test_client: TestClient, generator: DataGenerator):
    """Test that an application without view_notification permission cannot get notifications"""
    user = generator.gen_user(email="user@test.com")
    application = generator.gen_application(permissions=[])
    response = test_client.get(
        f"/v1/users/{user.id}/notifications", headers={"Authorization": f"Bearer {application.api_key}"}
    )
    assert response.status_code == 403


def test_get_notifications_user_with_permissions(
    test_client: TestClient, generator: DataGenerator, create_session_cookie: Callable[[int], str]
):
    """Test that a user with view_notification permission can get notifications"""
    user = generator.gen_user(email="user@test.com")
    notification = generator.gen_notification(user=user)
    authenticate_user(test_client, user, generator, create_session_cookie)
    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/users/{user.id}/notifications", headers={"X-CSRF-Token": "1"}),
        Permission.view_notification,
    )
    assert response.status_code == 200
    json_ = response.json()
    assert json_.get("count") == 1
    assert len(json_.get("notifications", [])) == 1
    assert json_["notifications"][0]["id"] == notification.id


def test_get_notifications_app_with_permissions(test_client: TestClient, generator: DataGenerator):
    """Test that an application with view_notification permission can get notifications"""
    user = generator.gen_user(email="user@test.com")
    notification = generator.gen_notification(user=user)
    application = generator.gen_application(permissions=[Permission.view_notification])
    response = test_client.get(
        f"/v1/users/{user.id}/notifications", headers={"Authorization": f"Bearer {application.api_key}"}
    )
    assert response.status_code == 200
    json_ = response.json()
    assert json_.get("count") == 1
    assert len(json_.get("notifications", [])) == 1
    assert json_["notifications"][0]["id"] == notification.id


### Begin NOTE:
# The /v1/users/me/notifications/{notification.id}/dismiss endpoint doesn't change behavior
# based on whether authentication is required or not.
# It always requires a user to be authenticated and doesn't allow an application,
# because posting to a /me-based endpoint just doesn't make sense outside of an authenticated user context


def test_dismiss_own_notification_unauthenticated(test_client: TestClient, generator: DataGenerator):
    """Test that dismissing a notification without authentication returns 401"""
    user = generator.gen_user(email="unauth@test.com")
    notification = generator.gen_notification(user=user)

    response = test_client.post(f"/v1/users/me/notifications/{notification.id}/dismiss")
    assert response.status_code == 401


def test_dismiss_own_notification_authenticated_user(
    test_client: TestClient, generator: DataGenerator, create_session_cookie: Callable[[int], str]
):
    """Test that an authenticated user can dismiss their own notification"""
    user = generator.gen_user(email="user@test.com")
    notification = generator.gen_notification(user=user)
    authenticate_user(test_client, user, generator, create_session_cookie)
    response = test_client.post(f"/v1/users/me/notifications/{notification.id}/dismiss", headers={"X-CSRF-Token": "1"})
    assert response.status_code == 200
    json_ = response.json()
    assert json_["id"] == notification.id
    assert json_["dismissed_at"] is not None


def test_dismiss_own_notification_authenticated_app(test_client: TestClient, generator: DataGenerator):
    """Test that an authenticated application is forbidden from /me-based notification endpoints"""
    application = generator.gen_application(permissions=["change_notification"])
    response = test_client.post(
        "/v1/users/me/notifications/1/dismiss", headers={"Authorization": f"Bearer {application.api_key}"}
    )
    assert response.status_code == 403


### End NOTE


def test_get_multiple_notifications(
    test_client: TestClient,
    generator: DataGenerator,
    create_session_cookie: Callable[[int], str],
):
    """Test getting all notifications for a user"""
    user = generator.gen_user(email="notifications@test.com")
    notification1 = generator.gen_notification(
        user=user,
        notification_type=NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW,
        target_url="/snaps/1",
    )
    notification2 = generator.gen_notification(
        user=user,
        notification_type=NotificationType.USER_ASSIGNED_ENVIRONMENT_REVIEW,
        target_url="/images/2",
        dismissed_at=datetime.now(),
    )

    authenticate_user(test_client, user, generator, create_session_cookie)
    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/users/{user.id}/notifications", headers={"X-CSRF-Token": "1"}),
        Permission.view_notification,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["notifications"]) == 2
    assert data["notifications"][0]["id"] in [notification1.id, notification2.id]
    assert data["notifications"][1]["id"] in [notification1.id, notification2.id]
    assert data["count"] == 2
    assert data["limit"] == 50
    assert data["offset"] == 0


def test_get_notification_for_nonexistent_user(
    test_client: TestClient, generator: DataGenerator, create_session_cookie: Callable[[int], str]
):
    """Test that getting notifications for a non-existent user returns 404"""
    user = generator.gen_user(email="user@test.com")
    authenticate_user(test_client, user, generator, create_session_cookie)
    response = make_authenticated_request(
        lambda: test_client.get("/v1/users/99999/notifications", headers={"X-CSRF-Token": "1"}),
        Permission.view_notification,
    )
    assert response.status_code == 404


def test_get_count_for_nonexistent_user(
    test_client: TestClient, generator: DataGenerator, create_session_cookie: Callable[[int], str]
):
    """Test that getting notification count for a non-existent user returns 404"""
    user = generator.gen_user(email="user@test.com")
    authenticate_user(test_client, user, generator, create_session_cookie)
    response = make_authenticated_request(
        lambda: test_client.get("/v1/users/99999/notifications/count", headers={"X-CSRF-Token": "1"}),
        Permission.view_notification,
    )
    assert response.status_code == 404


def test_get_unread_count(
    test_client: TestClient,
    generator: DataGenerator,
    create_session_cookie: Callable[[int], str],
):
    """Test getting unread notification count"""
    user = generator.gen_user(email="unread@test.com")
    generator.gen_notification(user=user)
    generator.gen_notification(user=user)
    generator.gen_notification(user=user, dismissed_at=datetime.now())

    authenticate_user(test_client, user, generator, create_session_cookie)
    response = make_authenticated_request(
        lambda: test_client.get(
            f"/v1/users/{user.id}/notifications/count?unread_only=true", headers={"X-CSRF-Token": "1"}
        ),
        Permission.view_notification,
    )

    assert response.status_code == 200
    assert response.json() == 2


def test_mark_notification_as_read_without_auth(test_client: TestClient, generator: DataGenerator):
    """Test that marking notification as read without auth returns 403"""
    user = generator.gen_user(email="mark-no-auth@test.com")
    notification = generator.gen_notification(user=user)

    response = test_client.post(f"/v1/users/{user.id}/notifications/{notification.id}/dismiss")
    assert response.status_code == 403


def test_mark_notification_as_read(
    test_client: TestClient,
    generator: DataGenerator,
    create_session_cookie: Callable[[int], str],
):
    """Test marking a notification as read"""
    user = generator.gen_user(email="mark-read@test.com")
    notification = generator.gen_notification(user=user)

    assert notification.dismissed_at is None

    authenticate_user(test_client, user, generator, create_session_cookie)
    response = make_authenticated_request(
        lambda: test_client.post(
            f"/v1/users/{user.id}/notifications/{notification.id}/dismiss", headers={"X-CSRF-Token": "1"}
        ),
        Permission.change_notification,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == notification.id
    assert data["dismissed_at"] is not None


def test_mark_notification_as_read_nonexistent_user(
    test_client: TestClient,
    generator: DataGenerator,
    create_session_cookie: Callable[[int], str],
):
    """Test that marking a notification as read for a non-existent user returns 404"""
    user = generator.gen_user(email="user@test.com")
    authenticate_user(test_client, user, generator, create_session_cookie)
    response = make_authenticated_request(
        lambda: test_client.post("/v1/users/99999/notifications/1/dismiss", headers={"X-CSRF-Token": "1"}),
        Permission.change_notification,
    )
    assert response.status_code == 404


def test_mark_nonexistent_notification_as_read(
    test_client: TestClient,
    generator: DataGenerator,
    create_session_cookie: Callable[[int], str],
):
    """Test marking a non-existent notification as read returns 404"""
    user = generator.gen_user(email="nonexistent@test.com")

    authenticate_user(test_client, user, generator, create_session_cookie)
    response = make_authenticated_request(
        lambda: test_client.post(f"/v1/users/{user.id}/notifications/99999/dismiss", headers={"X-CSRF-Token": "1"}),
        Permission.change_notification,
    )

    assert response.status_code == 404


def test_get_notifications_with_pagination(
    test_client: TestClient,
    generator: DataGenerator,
    create_session_cookie: Callable[[int], str],
):
    """Test getting notifications with limit and offset"""
    user = generator.gen_user(email="pagination@test.com")

    # Create 5 notifications with different artefact families
    notifications: list[Notification] = []
    families = ["snaps", "images", "debs", "charms", "snaps"]
    for idx, family in enumerate(families):
        notification = generator.gen_notification(
            user=user,
            notification_type=NotificationType.USER_ASSIGNED_ARTEFACT_REVIEW,
            target_url=f"/{family}/{idx}",
        )
        notifications.append(notification)

    authenticate_user(test_client, user, generator, create_session_cookie)

    # Test limit
    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/users/{user.id}/notifications?limit=2", headers={"X-CSRF-Token": "1"}),
        Permission.view_notification,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["notifications"]) == 2
    assert data["count"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 0

    # Test offset
    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/users/{user.id}/notifications?limit=2&offset=2", headers={"X-CSRF-Token": "1"}),
        Permission.view_notification,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["notifications"]) == 2
    assert data["count"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 2

    # Test offset beyond results
    response = make_authenticated_request(
        lambda: test_client.get(f"/v1/users/{user.id}/notifications?limit=10&offset=3", headers={"X-CSRF-Token": "1"}),
        Permission.view_notification,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["notifications"]) == 2
    assert data["count"] == 5
    assert data["limit"] == 10
    assert data["offset"] == 3
