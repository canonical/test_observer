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

import json
from base64 import b64encode
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import itsdangerous
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette import status

from test_observer.common.config import SESSIONS_SECRET
from test_observer.controllers.auth import swift_proxy
from test_observer.data_access.models import Team, User, UserSession
from test_observer.data_access.setup import get_db
from test_observer.main import app


def test_keystone_session_uses_bounded_timeout_and_connect_retries(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(swift_proxy, "_keystone_session", None)
    monkeypatch.setattr(
        swift_proxy.keystone_session.Session,
        "get_token",
        lambda _session: "test-token",
    )
    monkeypatch.setenv("OS_AUTH_URL", "https://keystone.example/v3")
    monkeypatch.setenv("OS_USERNAME", "reader")
    monkeypatch.setenv("OS_PASSWORD", "password")
    monkeypatch.setenv("OS_PROJECT_NAME", "project")

    assert swift_proxy.get_keystone_token() == "test-token"
    assert swift_proxy._keystone_session is not None
    assert swift_proxy._keystone_session.timeout == swift_proxy.KEYSTONE_REQUEST_TIMEOUT_SECONDS
    assert swift_proxy._keystone_session._connect_retries == swift_proxy.KEYSTONE_CONNECT_RETRIES


@pytest.fixture
def local_test_client(db_session: Session, monkeypatch: pytest.MonkeyPatch):
    """Test the auth-request route as a loopback nginx subrequest."""
    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = lambda: db_session
    monkeypatch.setattr(swift_proxy, "SWIFT_PROXY_AUTH_SECRET", "trusted-secret")
    with TestClient(app, client=("127.0.0.1", 50000)) as client:
        client.headers["X-Swift-Proxy-Auth"] = "trusted-secret"
        yield client
    if previous_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous_override


def _session_cookie(session_id: int) -> str:
    signer = itsdangerous.TimestampSigner(str(SESSIONS_SECRET))
    encoded = b64encode(json.dumps({"id": session_id}).encode()).decode()
    return signer.sign(encoded).decode()


def _make_user_session(db_session: Session, *, team_name: str | None, expired: bool = False) -> UserSession:
    user = User(email="swift-user@example.com", name="Swift User")
    if team_name:
        user.teams.append(Team(name=team_name, permissions=[]))
    db_session.add(user)
    db_session.flush()
    expires_at = datetime.now() - timedelta(days=1) if expired else datetime.now() + timedelta(days=1)
    session = UserSession(user_id=user.id, expires_at=expires_at)
    db_session.add(session)
    db_session.flush()
    return session


def test_unauthenticated_subrequest_provides_same_origin_login_url(
    local_test_client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(swift_proxy, "SWIFT_PROXY_ENABLED", True)
    monkeypatch.setattr(swift_proxy, "SAML_SP_BASE_URL", "https://test-observer-api.example.com")

    response = local_test_client.get(
        "/_internal/swift-proxy/authorize",
        headers={"X-Original-URI": "/v1/swift/charm-qa/artifact.tar?download=1"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    login_url = urlsplit(response.headers["X-Swift-Login-URL"])
    assert login_url.netloc == "test-observer-api.example.com"
    assert login_url.path == "/v1/auth/saml/login"
    return_to = parse_qs(login_url.query)["return_to"][0]
    assert return_to == ("https://test-observer-api.example.com/v1/swift/charm-qa/artifact.tar?download=1")


def test_login_url_accepts_exact_swift_root(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(swift_proxy, "SAML_SP_BASE_URL", "https://test-observer-api.example.com")

    login_url = urlsplit(swift_proxy._login_url("/v1/swift"))

    assert parse_qs(login_url.query)["return_to"] == ["https://test-observer-api.example.com/v1/swift"]


@pytest.mark.parametrize(
    "original_uri",
    [
        "https://attacker.example/v1/swift/charm-qa/artifact.tar",
        "/v1/swift/%2e%2e/private",
    ],
)
def test_login_redirect_rejects_unsafe_original_uri(
    local_test_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    original_uri: str,
):
    monkeypatch.setattr(swift_proxy, "SWIFT_PROXY_ENABLED", True)
    monkeypatch.setattr(swift_proxy, "SAML_SP_BASE_URL", "https://test-observer-api.example.com")

    response = local_test_client.get(
        "/_internal/swift-proxy/authorize",
        headers={"X-Original-URI": original_uri},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.parametrize("required_team", ["swift", "swift-proxy-readers"])
def test_configured_team_gets_keystone_token_without_csrf_header(
    local_test_client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    required_team: str,
):
    monkeypatch.setattr(swift_proxy, "SWIFT_PROXY_ENABLED", True)
    monkeypatch.setattr(swift_proxy, "SWIFT_PROXY_TEAM", required_team)
    monkeypatch.setattr(swift_proxy, "get_keystone_token", lambda: "keystone-token")
    session = _make_user_session(db_session, team_name=required_team)

    response = local_test_client.get(
        "/_internal/swift-proxy/authorize",
        headers={
            "Cookie": f"session={_session_cookie(session.id)}",
            "X-Original-URI": "/v1/swift/charm-qa/artifact.tar",
        },
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.headers["X-Keystone-Token"] == "keystone-token"


def test_keystone_timeout_returns_bad_gateway(
    local_test_client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(swift_proxy, "SWIFT_PROXY_ENABLED", True)
    monkeypatch.setattr(swift_proxy, "SWIFT_PROXY_TEAM", "swift")

    def raise_timeout() -> str:
        raise TimeoutError

    monkeypatch.setattr(swift_proxy, "get_keystone_token", raise_timeout)
    session = _make_user_session(db_session, team_name="swift")

    response = local_test_client.get(
        "/_internal/swift-proxy/authorize",
        headers={
            "Cookie": f"session={_session_cookie(session.id)}",
            "X-Original-URI": "/v1/swift/charm-qa/artifact.tar",
        },
    )

    assert response.status_code == status.HTTP_502_BAD_GATEWAY


def test_user_outside_configured_team_is_forbidden(
    local_test_client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(swift_proxy, "SWIFT_PROXY_ENABLED", True)
    monkeypatch.setattr(swift_proxy, "SWIFT_PROXY_TEAM", "swift")
    session = _make_user_session(db_session, team_name="other-team")

    response = local_test_client.get(
        "/_internal/swift-proxy/authorize",
        headers={
            "Cookie": f"session={_session_cookie(session.id)}",
            "X-Original-URI": "/v1/swift/charm-qa/artifact.tar",
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "X-Keystone-Token" not in response.headers


def test_expired_session_requires_saml_login(
    local_test_client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(swift_proxy, "SWIFT_PROXY_ENABLED", True)
    session = _make_user_session(db_session, team_name="swift", expired=True)

    response = local_test_client.get(
        "/_internal/swift-proxy/authorize",
        headers={
            "Cookie": f"session={_session_cookie(session.id)}",
            "X-Original-URI": "/v1/swift/charm-qa/artifact.tar",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "X-Swift-Login-URL" in response.headers


def test_auth_subrequest_rejects_non_loopback_clients(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(swift_proxy, "SWIFT_PROXY_ENABLED", True)
    with TestClient(app, client=("192.0.2.10", 50000)) as client:
        response = client.get(
            "/_internal/swift-proxy/authorize",
            headers={"X-Original-URI": "/v1/swift/charm-qa/artifact.tar"},
        )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_auth_subrequest_rejects_loopback_without_nginx_secret(
    local_test_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(swift_proxy, "SWIFT_PROXY_ENABLED", True)

    response = local_test_client.get(
        "/_internal/swift-proxy/authorize",
        headers={"X-Swift-Proxy-Auth": ""},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
