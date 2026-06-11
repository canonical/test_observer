# Copyright 2025 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import json
from base64 import b64decode
from collections.abc import Mapping
from datetime import datetime, timedelta
from html.parser import HTMLParser
from unittest.mock import MagicMock
from urllib.parse import urlsplit, urlunsplit

import itsdangerous
import pytest
import requests
from sqlalchemy.orm import Session
from urllib3.connectionpool import ConnectionPool

from test_observer.common.config import SESSIONS_SECRET
from test_observer.controllers.auth import saml
from test_observer.data_access.models import Team, User, UserSession
from test_observer.data_access.repository import get_or_create
from test_observer.data_access.setup import SessionLocal
from test_observer.external_apis.launchpad.models import LaunchpadUser

# The SP redirects to the IdP's publicly configured URL (SSP_BASE_URL_PATH).
# That address is reachable when tests run on the host, but not from inside the
# api container (where the IdP is the 'saml-idp' compose service on port 80).
IDP_PUBLIC_NETLOC = "localhost:8080"
IDP_INTERNAL_URL = "http://saml-idp"


def _idp_rewrite_target() -> str | None:
    """Return an IdP base URL to rewrite the public netloc to.

    Returns None when the public address is reachable (host runs), so the test
    talks to the IdP unchanged. Returns the in-network service URL when the
    public address is unreachable (running inside the api container).
    """
    try:
        requests.get(f"http://{IDP_PUBLIC_NETLOC}/simplesaml/", timeout=2, allow_redirects=False)
        return None
    except requests.exceptions.RequestException:
        return IDP_INTERNAL_URL


class _IdPRewriteAdapter(requests.adapters.HTTPAdapter):
    """Routes requests for the IdP's public netloc to a reachable address.

    The request URL (and therefore ``response.url`` and any redirects derived
    from it) is left pointing at the public netloc so the multi-step SAML flow
    stays internally consistent; only the underlying TCP connection is
    redirected, with the original Host header preserved so SimpleSAMLphp serves
    its configured base URL.
    """

    def __init__(self, target: str):
        self._target = urlsplit(target)
        super().__init__()

    def _route(self, url: str) -> str:
        parts = urlsplit(url)
        if parts.netloc == IDP_PUBLIC_NETLOC:
            return urlunsplit(parts._replace(scheme=self._target.scheme, netloc=self._target.netloc))
        return url

    def send(self, request: requests.PreparedRequest, **kwargs: object) -> requests.Response:  # type: ignore[override]
        if urlsplit(request.url).netloc == IDP_PUBLIC_NETLOC:
            # Connection is routed to the internal host below, so pin the Host
            # header to the public netloc SimpleSAMLphp expects.
            request.headers["Host"] = IDP_PUBLIC_NETLOC
        return super().send(request, **kwargs)  # type: ignore[arg-type]

    def get_connection_with_tls_context(  # type: ignore[override]
        self,
        request: requests.PreparedRequest,
        verify: bool | str | None,
        proxies: Mapping[str, str] | None = None,
        cert: tuple[str, str] | str | None = None,
    ) -> ConnectionPool:
        original = request.url
        if original is not None:
            request.url = self._route(original)
        try:
            return super().get_connection_with_tls_context(request, verify, proxies=proxies, cert=cert)
        finally:
            request.url = original

    def get_connection(self, url: str, proxies: Mapping[str, str] | None = None) -> ConnectionPool:  # type: ignore[override]
        return super().get_connection(self._route(url), proxies=proxies)


def _make_idp_session() -> requests.Session:
    """Create a requests session that can reach the IdP from host or container."""
    session = requests.Session()
    target = _idp_rewrite_target()
    if target:
        session.mount(f"http://{IDP_PUBLIC_NETLOC}", _IdPRewriteAdapter(target))
    return session


@pytest.fixture()
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SimpleFormParser(HTMLParser):
    """Simple HTML parser to extract form data"""

    def __init__(self):
        super().__init__()
        self.inputs = {}
        self.in_form = False

    def handle_starttag(self, tag: str, attrs: list):
        attrs_dict = dict(attrs)

        if tag == "form":
            self.in_form = True

        elif tag == "input" and self.in_form:
            name = attrs_dict.get("name")
            value = attrs_dict.get("value", "")
            if name:
                self.inputs[name] = value

    def handle_endtag(self, tag: str):
        if tag == "form":
            self.in_form = False


class TestSAMLAuthentication:
    """Test SAML authentication workflow"""

    CREDENTIALS = {"username": "mark", "password": "password"}

    def test_complete_saml_flow(self, db_session: Session):
        """Test our SAML Service Provider (SP) implementation with end-to-end workflow

        This test focuses on validating our SP behavior:
        - SAML login initiation and redirect generation
        - ACS endpoint SAML response processing
        - User data extraction and response formatting
        - SAML logout and session clearing

        Uses a SimpleSAMLPHP IdP for integration testing
        """
        # Use a persistent session to maintain cookies and state throughout entire flow
        self.session = _make_idp_session()
        self.api_url = "http://localhost:30000"
        self.db_session = db_session

        sso_url = self._initiate_saml_login()
        auth_state, login_form_url = self._fetch_and_parse_login_form(sso_url)
        auth_response = self._submit_credentials(auth_state, login_form_url)
        api_response = self._process_saml_response(auth_response)
        self._verify_session(api_response)
        self._logout_and_verify_session_cleared()

    def _initiate_saml_login(self) -> str:
        response = self.session.get(f"{self.api_url}/v1/auth/saml/login", allow_redirects=False)
        # Test our SP: should redirect to IdP for authentication
        assert response.status_code == 307
        assert "location" in response.headers
        return response.headers["location"]

    def _fetch_and_parse_login_form(self, idp_url: str) -> tuple[str, str]:
        idp_response = self.session.get(idp_url, allow_redirects=True)

        parser = SimpleFormParser()
        parser.feed(idp_response.text)

        return parser.inputs["AuthState"], idp_response.url

    def _submit_credentials(self, auth_state: str, login_form_url: str) -> requests.Response:
        login_data = {**self.CREDENTIALS, "AuthState": auth_state}
        return self.session.post(login_form_url, data=login_data, allow_redirects=False)

    def _process_saml_response(self, auth_response: requests.Response) -> requests.Response:
        parser = SimpleFormParser()
        parser.feed(auth_response.text)

        return self.session.post(
            f"{self.api_url}/v1/auth/saml/acs",
            data={
                "SAMLResponse": parser.inputs.get("SAMLResponse"),
                "RelayState": parser.inputs.get("RelayState"),
            },
        )

    def _verify_session(self, response: requests.Response) -> None:
        assert response.status_code == 200
        assert "session" in response.cookies

        signer = itsdangerous.TimestampSigner(str(SESSIONS_SECRET))
        session = json.loads(b64decode(signer.unsign(response.cookies["session"])))
        assert "id" in session

        session = self.db_session.get(UserSession, session["id"])
        assert session
        assert session.expires_at < datetime.now() + timedelta(days=14)
        self._session_id = session.id

        user = session.user
        assert user
        assert user.name == "Mark"
        assert user.email == "mark@electricdemon.com"
        # The compose stack runs with USE_LOCAL_LOGIN=true, so the SAML flow
        # skips the Launchpad lookup and no launchpad handle is recorded.
        assert user.launchpad_handle is None

    def _logout_and_verify_session_cleared(self) -> None:
        logout_response = self.session.get(
            f"{self.api_url}/v1/auth/saml/logout",
            headers={"X-CSRF-Token": "test"},
            allow_redirects=False,
        )

        assert logout_response.status_code == 307
        assert "location" in logout_response.headers

        logout_url = logout_response.headers["location"]
        self.session.get(logout_url, headers={"X-CSRF-Token": "test"})

        session = self.db_session.get(UserSession, self._session_id)
        assert session is None

    def _create_session_and_login(self) -> requests.Response:
        self.session = _make_idp_session()

        sso_url = self._initiate_saml_login()
        auth_state, login_form_url = self._fetch_and_parse_login_form(sso_url)
        auth_response = self._submit_credentials(auth_state, login_form_url)
        login_response = self._process_saml_response(auth_response)

        return login_response

    def test_team_membership_persists_after_login(self, db_session: Session):
        """Test that team membership persists after user logs in again

        This test verifies that when a user is added to a team, their membership
        is maintained even after logging in again. The SAML _create_user function
        should preserve existing team memberships when reassigning teams from
        SAML attributes.
        """
        self.api_url = "http://localhost:30000"
        self.db_session = db_session

        # Create user by logging in for the first time
        login_response = self._create_session_and_login()
        assert login_response.status_code == 200

        # Get user from database
        user = db_session.query(User).filter_by(email="mark@electricdemon.com").first()
        assert user is not None
        assert user.name == "Mark"

        # Create a team
        test_team = get_or_create(
            db_session,
            Team,
            {"name": "test-team"},
            {"permissions": [], "artefact_matching_rules": []},
        )
        db_session.commit()

        # Add user to the team
        if user not in test_team.members:
            test_team.members.append(user)
            db_session.commit()

        # Verify user is in the team
        db_session.refresh(user)
        team_names = [t.name for t in user.teams]
        assert "test-team" in team_names

        # Log the user in again (create a new session to make it a fresh login)
        second_login_response = self._create_session_and_login()
        assert second_login_response.status_code == 200

        # User should still belong to the team
        db_session.refresh(user)
        team_names_after_login = [t.name for t in user.teams]
        assert "test-team" in team_names_after_login, (
            f"User should be in test-team after login. Teams: {team_names_after_login}"
        )


def _build_auth(email: str, fullname: str) -> MagicMock:
    """Build a stub SAML auth object exposing the bits _create_user uses."""
    auth = MagicMock()
    auth.get_nameid.return_value = email
    auth.get_attributes.return_value = {"fullname": [fullname]}
    return auth


class TestCreateUserLocalLogin:
    """Unit tests for _create_user's USE_LOCAL_LOGIN branch."""

    def test_local_login_skips_launchpad_lookup(self, db_session: Session, monkeypatch: pytest.MonkeyPatch):
        """When USE_LOCAL_LOGIN is enabled, Launchpad is not queried."""
        monkeypatch.setattr(saml, "USE_LOCAL_LOGIN", True)
        # Fail loudly if the Launchpad API is constructed at all.
        launchpad_api = MagicMock(side_effect=AssertionError("LaunchpadAPI should not be used"))
        monkeypatch.setattr(saml, "LaunchpadAPI", launchpad_api)

        auth = _build_auth("local.user@example.com", "Local User")
        user = saml._create_user(db_session, auth)

        launchpad_api.assert_not_called()
        assert user.email == "local.user@example.com"
        assert user.name == "Local User"
        assert user.launchpad_handle is None
        assert user.teams == []

    def test_local_login_creates_user_without_teams(self, db_session: Session, monkeypatch: pytest.MonkeyPatch):
        """A new user is persisted with no team membership in local login mode."""
        monkeypatch.setattr(saml, "USE_LOCAL_LOGIN", True)

        auth = _build_auth("another.user@example.com", "Another User")
        user = saml._create_user(db_session, auth)

        persisted = db_session.query(User).filter_by(email="another.user@example.com").one()
        assert persisted.id == user.id
        assert persisted.launchpad_handle is None
        assert persisted.teams == []


class TestCreateUserLaunchpadLogin:
    """Unit tests for _create_user's Launchpad branch (USE_LOCAL_LOGIN disabled)."""

    def test_launchpad_lookup_populates_handle_and_teams(self, db_session: Session, monkeypatch: pytest.MonkeyPatch):
        """When USE_LOCAL_LOGIN is disabled, Launchpad data drives handle/teams."""
        monkeypatch.setattr(saml, "USE_LOCAL_LOGIN", False)

        lp_user = LaunchpadUser(
            handle="john-doe",
            email="john.doe@canonical.com",
            name="John Doe",
            teams=["canonical", "hw-cert"],
        )
        launchpad_instance = MagicMock()
        launchpad_instance.get_user_by_email.return_value = lp_user
        monkeypatch.setattr(saml, "LaunchpadAPI", MagicMock(return_value=launchpad_instance))

        auth = _build_auth("john.doe@canonical.com", "John Doe")
        user = saml._create_user(db_session, auth)

        launchpad_instance.get_user_by_email.assert_called_once_with("john.doe@canonical.com")
        assert user.launchpad_handle == "john-doe"
        assert {t.name for t in user.teams} == {"canonical", "hw-cert"}

    def test_launchpad_lookup_without_match_leaves_user_bare(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        """An unknown Launchpad user still creates a user with no handle/teams."""
        monkeypatch.setattr(saml, "USE_LOCAL_LOGIN", False)

        launchpad_instance = MagicMock()
        launchpad_instance.get_user_by_email.return_value = None
        monkeypatch.setattr(saml, "LaunchpadAPI", MagicMock(return_value=launchpad_instance))

        auth = _build_auth("unknown@example.com", "Unknown User")
        user = saml._create_user(db_session, auth)

        assert user.launchpad_handle is None
        assert user.teams == []
