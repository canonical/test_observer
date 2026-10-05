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

"""Private nginx auth-request endpoint for Swift object access."""

import hmac
import logging
import os
import posixpath
import threading
import urllib.parse
from datetime import datetime

from anyio import to_thread
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from keystoneauth1 import session as keystone_session
from keystoneauth1.identity import v3
from sqlalchemy.orm import Session, selectinload
from starlette import status

from test_observer.common.config import SAML_SP_BASE_URL
from test_observer.data_access.models import User, UserSession
from test_observer.data_access.setup import get_db

logger = logging.getLogger("test-observer-backend")
KEYSTONE_REQUEST_TIMEOUT_SECONDS = 10
KEYSTONE_CONNECT_RETRIES = 1

router = APIRouter()

SWIFT_PROXY_ENABLED = os.getenv("SWIFT_PROXY_ENABLED", "false").lower() == "true"
SWIFT_PROXY_AUTH_SECRET = os.getenv("SWIFT_PROXY_AUTH_SECRET", "")
SWIFT_PROXY_TEAM = os.getenv("SWIFT_PROXY_TEAM", "swift")

_token_lock = threading.Lock()
_keystone_session: keystone_session.Session | None = None


def get_keystone_token() -> str:
    """Return a cached Keystone token, refreshing it when Keystone requires."""
    global _keystone_session  # noqa: PLW0603

    with _token_lock:
        if _keystone_session is None:
            password = os.getenv("OS_PASSWORD", "")
            if not password:
                raise RuntimeError("OS_PASSWORD is not configured")

            auth = v3.Password(
                auth_url=os.environ["OS_AUTH_URL"],
                username=os.environ["OS_USERNAME"],
                password=password,
                project_name=os.environ["OS_PROJECT_NAME"],
                user_domain_name=os.getenv("OS_USER_DOMAIN_NAME", "Default"),
                project_domain_name=os.getenv("OS_PROJECT_DOMAIN_NAME", "Default"),
            )
            _keystone_session = keystone_session.Session(
                auth=auth,
                timeout=KEYSTONE_REQUEST_TIMEOUT_SECONDS,
                connect_retries=KEYSTONE_CONNECT_RETRIES,
                status_code_retries=0,
            )

        token = _keystone_session.get_token()
        if not token:
            raise RuntimeError("Keystone returned an empty token")
        return str(token)


def _login_url(original_uri: str) -> str:
    """Build the Test Observer SAML login URL for a safe Swift return path."""
    parsed = urllib.parse.urlsplit(original_uri)
    decoded_path = urllib.parse.unquote(parsed.path)
    normalized_path = posixpath.normpath(decoded_path)
    if (
        parsed.scheme
        or parsed.netloc
        or not decoded_path.startswith("/v1/swift/")
        or "\\" in decoded_path
        or "\x00" in decoded_path
        or any(ord(character) < 32 or ord(character) == 127 for character in decoded_path)
        or any(segment in {".", ".."} for segment in decoded_path.split("/"))
        or not (
            normalized_path == "/v1/swift"
            or normalized_path.startswith("/v1/swift/")
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid original URI",
        )

    api_base = SAML_SP_BASE_URL.rstrip("/")
    return_to = f"{api_base}{original_uri}"
    query = urllib.parse.urlencode({"return_to": return_to})
    return f"{api_base}/v1/auth/saml/login?{query}"


@router.get("/_internal/swift-proxy/authorize", include_in_schema=False)
async def authorize_swift_proxy_request(
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    """Authorize nginx's internal subrequest and provide its Keystone token."""
    if not request.client or request.client.host not in {"127.0.0.1", "::1"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if not SWIFT_PROXY_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    provided_secret = request.headers.get("x-swift-proxy-auth", "")
    if not SWIFT_PROXY_AUTH_SECRET or not hmac.compare_digest(
        provided_secret,
        SWIFT_PROXY_AUTH_SECRET,
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    original_uri = request.headers.get("x-original-uri", "")
    login_url = _login_url(original_uri)
    session_id = request.session.get("id")
    if not session_id:
        return Response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"X-Swift-Login-URL": login_url},
        )

    user_session = db.get(
        UserSession,
        session_id,
        options=[selectinload(UserSession.user).selectinload(User.teams)],
    )
    if not user_session or user_session.expires_at < datetime.now():
        return Response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"X-Swift-Login-URL": login_url},
        )

    if not any(team.name == SWIFT_PROXY_TEAM for team in user_session.user.teams):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not in the required team")

    try:
        token = await to_thread.run_sync(get_keystone_token)
    except Exception as exc:
        logger.exception("Failed to obtain a Keystone token for the Swift proxy")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Swift storage authentication failed",
        ) from exc

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
        headers={"X-Keystone-Token": token},
    )
